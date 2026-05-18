"""
主智能体装配与异步执行入口。

架构：1 个总指挥 + 3 个子智能体；支持安全问答（按需调度）与完整研判出报告。
调用链：前端 -> POST /api/task -> run_deep_agent -> main_agent.astream
"""
import shutil
from pathlib import Path

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver

from agent.llm import model
from agent.prompts import main_agent_content
from agent.subagents.database_query_agent import database_query_agent
from agent.subagents.knowledge_base_agent import knowledge_base_agent
from agent.subagents.network_search_agent import network_search_agent
from api.context import reset_session_context, set_session_context, set_thread_context
from api.monitor import monitor

# 总指挥专属工具：只负责报告生成与读取上传文件，不负责查库/搜网
from tools.markdown_tools import generate_markdown
from tools.pdf_tools import convert_md_to_pdf
from tools.upload_file_read_tool import read_file_content

# 使用 DeepAgents 工厂创建主智能体
# - checkpointer：按 thread_id（即 session_id）做会话记忆
# - subagents：三个子智能体由总指挥通过 task 工具调度
main_agent = create_deep_agent(
    model=model,
    system_prompt=main_agent_content["system_prompt"],
    tools=[generate_markdown, convert_md_to_pdf, read_file_content],
    checkpointer=InMemorySaver(),
    subagents=[database_query_agent, network_search_agent, knowledge_base_agent],
)

# 项目根目录，用于拼接 output/session_{id}、updated/session_{id}
project_root_path = Path(__file__).resolve().parents[1]


async def run_deep_agent(task_query: str, session_id: str) -> None:
    """
    异步流式执行主智能体，并通过 monitor 向前端 WebSocket 推送进度。

    :param task_query: 用户在前端输入的研判任务描述
    :param session_id: 会话 ID（与 LangGraph thread_id、output 目录名一致）
    """
    # -------------------------------------------------------------------------
    # 1. 准备工作目录
    # session_dir：绝对路径，给 ContextVars / 前端静态资源访问
    # relative_session_dir_str：相对路径，拼进大模型提示词，约束文件落盘位置
    # -------------------------------------------------------------------------
    session_dir = project_root_path / "output" / f"session_{session_id}"
    session_dir.mkdir(parents=True, exist_ok=True)
    session_dir_str = str(session_dir).replace("\\", "/")
    relative_session_dir_str = str(session_dir.relative_to(project_root_path)).replace("\\", "/")

    # -------------------------------------------------------------------------
    # 2. 处理用户上传文件（updated/session_{id} -> 复制到 output/session_{id}）
    # -------------------------------------------------------------------------
    updated_dir_path = project_root_path / "updated" / f"session_{session_id}"
    updated_info_prompt = ""
    if updated_dir_path.exists():
        files = [f.name for f in updated_dir_path.iterdir() if f.is_file()]
        if files:
            for filename in files:
                # copy2 保留修改时间等元数据
                shutil.copy2(updated_dir_path / filename, session_dir / filename)
            updated_info_prompt = (
                "\n    [已上传文件] 已加载到工作目录:\n"
                + "\n".join(f"    - {f}" for f in files)
                + "\n    请优先使用 read_file_content 读取并参考这些文件。"
            )

    # -------------------------------------------------------------------------
    # 3. 写入 ContextVars，供工具层 get_session_context / get_thread_context 使用
    #    同时通知前端当前会话的工作目录
    # -------------------------------------------------------------------------
    session_dir_token = set_session_context(session_dir_str)
    session_id_token = set_thread_context(session_id)
    monitor.report_session_dir(session_dir_str)

    # LangGraph 配置：thread_id 与 session_id 绑定，实现多用户会话隔离
    config = {"configurable": {"thread_id": session_id}}

    # 工作环境指令：问答为主；仅完整研判且用户要文档时才生成报告
    path_instruction = f"""
    【工作环境指令 - 企业安全智能助手会话】
    工作目录: {relative_session_dir_str}
    {updated_info_prompt}

    规则：
    1. 默认【问答模式】：根据用户问题调度必要子智能体，在对话中直接回答；不要调用 generate_markdown / convert_md_to_pdf。
    2. 仅当用户明确要求完整研判且需要输出报告文件（PDF/Markdown/正式风险评估报告）时，进入【完整研判模式】，并在子智能体数据齐全后调用报告工具。
    3. 报告（Markdown/PDF）须保存到：'{relative_session_dir_str}/filename'，仅使用相对路径。
    4. 读取已上传文件：read_file_content 的 filename 不要带目录前缀。
    5. 总指挥禁止自行写文件；报告仅通过 generate_markdown → convert_md_to_pdf。
    """

    # -------------------------------------------------------------------------
    # 4. 流式执行主智能体
    # chunk 结构示例：{"model": {"messages": [...]}} 或 {"tools": {"messages": [...]}}
    # -------------------------------------------------------------------------
    try:
        async for chunk in main_agent.astream(
            {"messages": [{"role": "user", "content": task_query + path_instruction}]},
            config=config,
        ):
            for node_name, state in chunk.items():
                if not state or "messages" not in state:
                    continue
                messages = state["messages"]
                if not messages or not isinstance(messages, list):
                    continue
                last_msg = messages[-1]

                # 只处理 model 节点的输出（工具调用决策 & 最终自然语言回复）
                if node_name != "model":
                    continue

                if last_msg.tool_calls:
                    for tool_call in last_msg.tool_calls:
                        # 调度子智能体时，DeepAgents 使用 name='task' 的工具
                        # args 中包含 subagent_type（子智能体名）与 description（任务描述）
                        if tool_call["name"] == "task":
                            monitor.report_assistant(
                                tool_call["args"]["subagent_type"],
                                {"description": tool_call["args"]["description"]},
                            )
                elif last_msg.content:
                    # 总指挥最终回复，推送给前端（content 可能为 str 或多模态块列表）
                    content = last_msg.content
                    if not isinstance(content, str):
                        content = str(content)
                    monitor.report_task_result(content)

    except Exception as e:
        monitor._emit("error", f"执行主智能发生异常：{str(e)}")
    finally:
        # 请求结束必须 reset，避免 ContextVars 泄漏到下一个用户请求
        reset_session_context(session_dir_token, session_id_token)
