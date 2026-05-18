# 子智能体：合规法律法规知识库检索（本地 Milvus）
import os

from agent.prompts import sub_agents_content

# RAG_BACKEND=milvus  → 本地 Milvus + rawflow/ragdata

_backend = os.getenv("RAG_BACKEND", "milvus").lower()

if _backend == "milvus":
    from tools.local_rag_tools import create_ask_delete, get_assistant_list

knowledge_base_agent = {
    "name": sub_agents_content["knowledge_base_agent"]["name"],
    "description": sub_agents_content["knowledge_base_agent"]["description"],
    "system_prompt": sub_agents_content["knowledge_base_agent"]["system_prompt"],
    "tools": [get_assistant_list, create_ask_delete],
}
