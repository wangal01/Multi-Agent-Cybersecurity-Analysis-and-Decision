"""
本地 Milvus 向量库：MilvusClient + fastembed/openai 嵌入。

不依赖 langchain-milvus 的 ORM Collection，避免 pymilvus 2.6 的 ConnectionNotExistException。
"""
import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from pymilvus import MilvusClient

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _PROJECT_ROOT / ".env"

_DEFAULT_JSONL = (
    _PROJECT_ROOT
    / "rawflow"
    / "ragdata"
    / "Cybersecurity-High-Quality-Dataset"
    / "cleaned_2026-1-5-Cybersecurity-bigDataset_qualified_qualified.jsonl"
)

_TEXT_FIELD = "text"
_VECTOR_FIELD = "vector"


class _FastEmbedEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [vec.tolist() for vec in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(self._model.embed([text])).tolist()


def load_milvus_env() -> None:
    if _ENV_FILE.exists():
        load_dotenv(_ENV_FILE)
    else:
        load_dotenv()


def get_milvus_connection_params() -> dict:
    load_milvus_env()
    return {
        "host": os.getenv("MILVUS_HOST", "localhost"),
        "port": os.getenv("MILVUS_PORT", "19530"),
    }


def get_milvus_uri() -> str:
    p = get_milvus_connection_params()
    return os.getenv("MILVUS_URI", f"http://{p['host']}:{p['port']}")


def get_connection_args() -> dict:
    return {"uri": get_milvus_uri()}


def get_milvus_client() -> MilvusClient:
    return MilvusClient(uri=get_milvus_uri())


def get_collection_name() -> str:
    load_milvus_env()
    return os.getenv("MILVUS_COLLECTION", "cybersecurity_kb")


def get_default_jsonl_path() -> Path:
    load_milvus_env()
    custom = os.getenv("RAGDATA_JSONL_PATH")
    if custom:
        return Path(custom)
    return _DEFAULT_JSONL


def connect_milvus() -> MilvusClient:
    return get_milvus_client()


def get_embeddings() -> Embeddings:
    load_milvus_env()
    provider = os.getenv("EMBEDDING_PROVIDER", "fastembed").lower()
    model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=model_name if "embedding" in model_name else "text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_BASE_URL"),
        )

    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": os.getenv("EMBEDDING_DEVICE", "cpu")},
            encode_kwargs={"normalize_embeddings": True},
        )

    return _FastEmbedEmbeddings(model_name=model_name)


def drop_collection_if_exists(collection_name: Optional[str] = None) -> bool:
    name = collection_name or get_collection_name()
    client = get_milvus_client()
    if client.has_collection(name):
        client.drop_collection(name)
        return True
    return False


def _embedding_dim(embeddings: Embeddings) -> int:
    return len(embeddings.embed_query("dimension_probe"))


def ensure_collection(
    embeddings: Embeddings,
    collection_name: Optional[str] = None,
    recreate: bool = False,
) -> MilvusClient:
    """创建集合（向量维度自动探测）。"""
    name = collection_name or get_collection_name()
    client = get_milvus_client()
    if recreate and client.has_collection(name):
        client.drop_collection(name)
    if not client.has_collection(name):
        dim = _embedding_dim(embeddings)
        # pymilvus 2.6：create_collection 会同时建立默认向量索引（AUTOINDEX）
        client.create_collection(
            collection_name=name,
            dimension=dim,
            metric_type="COSINE",
            auto_id=True,
        )
    return client


def insert_documents(
    documents: list[Document],
    embeddings: Optional[Embeddings] = None,
    collection_name: Optional[str] = None,
) -> int:
    """批量写入文档与向量，返回写入条数。"""
    if not documents:
        return 0
    emb = embeddings or get_embeddings()
    name = collection_name or get_collection_name()
    client = get_milvus_client()
    if not client.has_collection(name):
        ensure_collection(emb, name, recreate=False)

    texts = [d.page_content for d in documents]
    vectors = emb.embed_documents(texts)
    rows: list[dict[str, Any]] = []
    for doc, vec in zip(documents, vectors):
        row: dict[str, Any] = {_TEXT_FIELD: doc.page_content, _VECTOR_FIELD: vec}
        if doc.metadata:
            # 勿使用字段名 id，会与 Milvus 主键 id 冲突
            row.update(
                {
                    k: v
                    for k, v in doc.metadata.items()
                    if k not in (_VECTOR_FIELD, "id")
                }
            )
            if doc.metadata.get("id") is not None:
                row["doc_id"] = str(doc.metadata["id"])
        rows.append(row)

    client.insert(collection_name=name, data=rows)
    return len(rows)


def similarity_search(
    query: str,
    k: int = 5,
    embeddings: Optional[Embeddings] = None,
    collection_name: Optional[str] = None,
) -> list[Document]:
    """向量相似度检索。"""
    emb = embeddings or get_embeddings()
    name = collection_name or get_collection_name()
    client = get_milvus_client()
    if not client.has_collection(name):
        return []

    qvec = emb.embed_query(query)
    # 动态字段中可能含 source、id 等
    results = client.search(
        collection_name=name,
        data=[qvec],
        limit=k,
        output_fields=["*"],
    )
    docs: list[Document] = []
    if not results:
        return docs
    for hit in results[0]:
        entity = hit.get("entity") or {}
        text = entity.get(_TEXT_FIELD, "")
        meta = {key: val for key, val in entity.items() if key not in (_TEXT_FIELD, _VECTOR_FIELD)}
        docs.append(Document(page_content=text, metadata=meta))
    return docs


def collection_exists() -> bool:
    return get_milvus_client().has_collection(get_collection_name())


def get_collection_stats() -> dict:
    name = get_collection_name()
    client = get_milvus_client()
    if not client.has_collection(name):
        return {"collection": name, "exists": False, "row_count": 0}
    try:
        stats = client.get_collection_stats(name)
        return {
            "collection": name,
            "exists": True,
            "row_count": int(stats.get("row_count", 0)),
        }
    except Exception as e:
        return {"collection": name, "exists": True, "row_count": -1, "error": str(e)}


def build_document(instruction: str, output: str, doc_id: Optional[str] = None) -> Document:
    text = f"【问题】\n{instruction.strip()}\n\n【答案】\n{output.strip()}"
    meta: dict[str, Any] = {"source": "Cybersecurity-High-Quality-Dataset"}
    if doc_id:
        meta["doc_id"] = str(doc_id)
    return Document(page_content=text, metadata=meta)


# 兼容旧代码：不再使用 langchain_milvus.Milvus
def get_vector_store():
    raise NotImplementedError(
        "已改用 MilvusClient 直连，请使用 similarity_search() / insert_documents()"
    )
