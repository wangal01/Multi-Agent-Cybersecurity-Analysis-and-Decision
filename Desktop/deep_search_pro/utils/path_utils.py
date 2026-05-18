"""
统一的文件路径解析工具。

为什么需要它？
- 大模型常生成 /workspace/xxx 等虚拟路径，若直接写入会落到错误目录。
- 多用户并发时，必须把文件锁定在 output/session_{thread_id} 下，防止串台与路径嵌套。

核心能力：
1. 清洗虚拟路径前缀（/workspace、/mnt/data、/home/user）
2. 识别 updated/ 上传目录，相对项目根目录解析
3. 结合 session_dir 处理相对/绝对路径
4. 防止 session_id 目录重复嵌套（如 session_abc/session_abc/file.md）
"""
import os
from pathlib import Path
from typing import Optional


def resolve_path(filename: str, session_dir: Optional[str] = None) -> str:
    """
    将大模型传入的 filename/path 解析为安全的绝对路径。

    :param filename: 文件名或路径（可能含虚拟前缀、相对路径）
    :param session_dir: 当前会话目录（来自 ContextVars），为 None 时相对 CWD 解析
    :return: 解析后的绝对路径字符串
    """
    path = Path(filename)
    path_str = filename.replace("\\", "/")  # 统一斜杠，便于字符串匹配

    # 1. 虚拟路径清洗：剥离大模型习惯的假绝对路径前缀
    virtual_prefixes = ["/workspace", "/mnt/data", "/home/user"]
    for prefix in virtual_prefixes:
        if path_str.startswith(prefix):
            cleaned = path_str[len(prefix) :].lstrip("/")
            path = Path(cleaned)
            path_str = str(path).replace("\\", "/")
            break

    # 2. 用户上传文件：路径中含 updated/ 时，相对于项目根目录解析
    if "updated/" in path_str:
        idx = path_str.find("updated/")
        relative_part = path_str[idx:]
        return str(Path(relative_part).resolve())

    # 无会话上下文时，直接 resolve（一般仅用于脚本调试）
    if not session_dir:
        return str(path.resolve())

    session_path = Path(session_dir).resolve()
    session_name = session_path.name  # 例如 session_a1b2c3

    # 3. 结合 session 目录处理绝对路径 / 相对路径
    is_unix_abs = path_str.startswith("/")

    if path.is_absolute() or (os.name == "nt" and is_unix_abs):
        # Windows：/foo 无盘符时视为相对 session 的路径
        if os.name == "nt" and is_unix_abs and not path.drive:
            full_path = session_path / path_str.lstrip("/")
        else:
            full_path = path.resolve()

        try:
            if session_path in full_path.parents or full_path == session_path:
                # 防止 .../session_xxx/session_xxx/report.md 双重嵌套
                parts = full_path.parts
                for i in range(len(parts) - 1):
                    if parts[i] == session_name and parts[i + 1] == session_name:
                        return str(session_path / full_path.name)
                return str(full_path)
        except Exception:
            pass

        return str(full_path)

    else:
        # 相对路径：若已含 session 名或 output/ 前缀，只取文件名拼到 session 根目录
        parts = path.parts
        if session_name in parts:
            return str(session_path / path.name)
        if parts and parts[0] == "output":
            return str(session_path / path.name)
        return str(session_path / path)
