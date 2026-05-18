"""
本地 Milvus RAG 工具（替代远程 RAGFlow，供 compliance 子智能体使用）。

前置条件：
1. Milvus 已启动（默认 localhost:19530）
2. 已执行 python scripts/ingest_ragdata_to_milvus.py 完成入库
3. .env 中 RAG_BACKEND=milvus
"""
from langchain_core.tools import tool

from api.monitor import monitor
from rawflow.milvus_store import (
    get_collection_stats,
    get_collection_name,
    get_default_jsonl_path,
    similarity_search,
)


@tool
def get_assistant_list() -> str:
    """
    查询本地 Milvus 知识库状态（兼容原 RAGFlow 工具名，供子智能体先调用）。
    返回集合名称、条目数、数据文件路径，供模型确认可向该库提问。
    """
    monitor.report_tool(tool_name="本地Milvus-知识库信息：get_assistant_list", args={})
    stats = get_collection_stats()
    jsonl = get_default_jsonl_path()
    lines = [
        "【本地 Milvus 合规/网络安全知识库】",
        f"助手名称: 网络安全合规知识库（本地）",
        f"功能介绍: 基于 Milvus 向量检索的网络安全高质量问答数据集，覆盖法规、等保、攻防与漏洞治理等主题。",
        f"向量集合: {stats.get('collection', get_collection_name())}",
        f"已入库向量约: {stats.get('row_count', '未知')!s} 条",
        f"数据源文件: {jsonl}",
        f"集合已创建: {'是' if stats.get('exists') else '否（请先运行 scripts/ingest_ragdata_to_milvus.py）'}",
    ]
    if stats.get("error"):
        lines.append(f"备注: {stats['error']}")
    return "\n".join(lines)


@tool
def create_ask_delete(chat_name: str, question: str) -> str:
    """
    在本地 Milvus 知识库中检索与问题相关的原始切片（兼容原 RAGFlow 工具名）。
    :param chat_name: 可填「网络安全合规知识库（本地）」或 get_assistant_list 返回的助手名
    :param question: 合规/法规/安全响应相关提问
    :return: 检索到的原文切片，供总指挥写入报告「合规依据」章节（勿概括）
    """
    monitor.report_tool(
        tool_name="本地Milvus-知识检索：create_ask_delete",
        args={"chat_name": chat_name, "question": question},
    )
    stats = get_collection_stats()
    if not stats.get("exists"):
        return (
            "本地 Milvus 集合尚未创建。请先启动 Milvus，并执行：\n"
            "  python scripts/ingest_ragdata_to_milvus.py\n"
            f"（默认集合名: {get_collection_name()}）"
        )

    top_k = 5
    try:
        docs = similarity_search(question, k=top_k)
    except Exception as e:
        return f"Milvus 检索失败: {str(e)}"

    if not docs:
        return f"未检索到与问题相关的内容：{question}"

    parts = [f"【本地 Milvus 检索结果】问题：{question}\n共 {len(docs)} 条切片：\n"]
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata or {}
        doc_id = meta.get("doc_id") or meta.get("id")
        id_suffix = f"id={doc_id}" if doc_id is not None and doc_id != "" else ""
        header = f"--- 切片 {i} {id_suffix} ---".rstrip()
        parts.append(header + "\n")
        parts.append(str(doc.page_content))
        parts.append("")
    return "\n".join(parts)
