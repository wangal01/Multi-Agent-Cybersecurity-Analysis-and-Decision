"""
Markdown 报告生成工具（总指挥专用）。
所有路径经 resolve_path 锁定到当前 session 的 output/session_{thread_id} 目录。
"""
from pathlib import Path

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from langchain_core.tools import tool

from api.context import get_session_context
from api.monitor import monitor
from utils.path_utils import resolve_path


@tool
def generate_markdown(
    content: Annotated[str, "要写入 Markdown 文档的完整报告正文"],
    filename: Annotated[str, "文件名（可带或不带 .md 后缀）"],
    path: Annotated[str, "相对工作目录的子路径，默认为空表示保存在会话根目录"] = "",
):
    """
    根据文本内容生成 Markdown 文件。
    调用前须已从子智能体拿到完整研判数据，禁止使用占位符内容。
    """
    monitor.report_tool("Markdown文档生成工具", {"filename": filename})

    if not filename.endswith(".md"):
        filename += ".md"

    # 从 ContextVars 获取当前请求的会话目录（在 run_deep_agent 中 set_session_context）
    session_dir = get_session_context()

    # 拼接 path + filename，再经 resolve_path 防止大模型路径幻觉
    if path and path != ".":
        full_input_path = str(Path(path) / filename)
    else:
        full_input_path = filename
    full_path_str = resolve_path(full_input_path, session_dir)
    file_path = Path(full_path_str)
    parent_dir = file_path.parent

    try:
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"Markdown文件 '{file_path}' 已成功生成并保存。"
    except Exception as e:
        return f"生成Markdown文件失败: {str(e)}"
