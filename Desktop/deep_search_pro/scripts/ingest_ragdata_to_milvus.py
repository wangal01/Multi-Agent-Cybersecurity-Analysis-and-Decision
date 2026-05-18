"""
将 rawflow/ragdata 下的 JSONL 写入本地 Milvus（MilvusClient 直连，兼容 pymilvus 2.6+）。
"""
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from tqdm import tqdm

from rawflow.milvus_store import (
    build_document,
    drop_collection_if_exists,
    ensure_collection,
    get_collection_name,
    get_default_jsonl_path,
    get_embeddings,
    get_milvus_uri,
    insert_documents,
    load_milvus_env,
)


def main() -> None:
    load_milvus_env()
    jsonl_path = get_default_jsonl_path()
    if not jsonl_path.exists():
        print(f"[错误] 数据文件不存在: {jsonl_path}")
        sys.exit(1)

    max_rows = int(os.getenv("INGEST_MAX_ROWS", "1000"))
    batch_size = int(os.getenv("INGEST_BATCH_SIZE", "64"))
    recreate = os.getenv("MILVUS_RECREATE", "true").lower() in ("1", "true", "yes")

    collection_name = get_collection_name()
    embeddings = get_embeddings()

    print(f"[配置] Milvus {get_milvus_uri()}  collection={collection_name}")
    print(f"[配置] 数据文件 {jsonl_path}")
    print(f"[配置] 最多入库 {max_rows if max_rows > 0 else '全量'} 条, batch={batch_size}")

    if recreate:
        drop_collection_if_exists(collection_name)
        print(f"[Milvus] 已删除旧集合（若存在）: {collection_name}")

    ensure_collection(embeddings, collection_name, recreate=False)
    print(f"[Milvus] 集合就绪: {collection_name}")

    batch: list = []
    total = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        iterator = tqdm(f, desc="读取 JSONL")
        for line in iterator:
            if max_rows > 0 and total >= max_rows:
                break
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            instruction = row.get("instruction") or ""
            output = row.get("output") or ""
            if not instruction and not output:
                continue

            batch.append(build_document(instruction, output, row.get("id")))

            if len(batch) >= batch_size:
                if max_rows > 0 and total + len(batch) > max_rows:
                    batch = batch[: max_rows - total]
                n = insert_documents(batch, embeddings, collection_name)
                total += n
                batch = []
                iterator.set_postfix(ingested=total)

    if batch:
        if max_rows > 0 and total + len(batch) > max_rows:
            batch = batch[: max_rows - total]
        if batch:
            total += insert_documents(batch, embeddings, collection_name)

    print(f"[完成] 共写入 {total} 条向量到集合 `{collection_name}`")


if __name__ == "__main__":
    main()
