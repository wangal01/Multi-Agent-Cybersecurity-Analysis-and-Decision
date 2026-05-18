"""
企业资产与漏洞台账 MySQL 查询工具。
供 database_query_agent 检索 company_assets、asset_vulnerabilities 等表。
"""
import os
import re

from dotenv import find_dotenv, load_dotenv
from mysql.connector import connect, Error
from langchain_core.tools import tool

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from api.monitor import monitor

load_dotenv(find_dotenv(usecwd=True))


def get_db_config():
    """从环境变量加载 MySQL 连接配置。"""
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "collation": os.getenv("MYSQL_COLLATION", "utf8mb4_unicode_ci"),
        "autocommit": True,
        "sql_mode": os.getenv("MYSQL_SQL_MODE", "TRADITIONAL"),
    }

    config = {k: v for k, v in config.items() if v is not None}
    required_keys = ["user", "password", "database"]
    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        raise ValueError(f"缺失数据库核心配置：{', '.join(missing_keys)}")
    return config


def _sanitize_table_name(table_name: str) -> str:
    """表名基础安全清洗：剥离反引号与分号，仅保留合法标识符。"""
    cleaned = table_name.replace("`", "").replace(";", "").strip()
    if not re.fullmatch(r"[a-zA-Z0-9_]+", cleaned):
        raise ValueError(f"非法表名：{table_name}")
    return cleaned


def _format_mysql_error(err: Error, config: dict) -> str:
    """将 MySQL 异常转为可操作的排查说明（不暴露密码）。"""
    errno = getattr(err, "errno", None)
    if errno == 1045:
        return (
            "MySQL 认证失败（Access denied）：.env 中的 MYSQL_USER / MYSQL_PASSWORD 与本地实例不一致。"
            f" 当前配置：user={config.get('user')}，host={config.get('host')}:{config.get('port')}，"
            f"database={config.get('database')}。"
            " 请用 MySQL 客户端或 Navicat 验证账号密码，修正 .env 后重启服务；"
            " 可运行：python scripts/test_mysql_connection.py"
        )
    if errno == 1049:
        return (
            f"数据库不存在：{config.get('database')}。"
            " 请先 CREATE DATABASE，再执行 sql/init_asset_vuln_db.sql"
        )
    if errno == 2003:
        return (
            f"无法连接 MySQL 服务（{config.get('host')}:{config.get('port')}）。"
            " 请确认 MySQL 服务已启动且端口正确。"
        )
    return str(err)


def _rows_to_csv(columns, rows) -> str:
    """将查询结果转为 CSV 文本，便于大模型阅读。"""
    header_str = ",".join(columns)
    data_str = "\n".join(",".join(map(str, row)) for row in rows)
    return f"{header_str}\n{data_str}" if data_str else header_str


@tool
def list_sql_tables() -> str:
    """
    列出当前漏洞台账库中所有可用的数据表。
    用于资产漏洞研判前确认可查询的表（通常为 company_assets、asset_vulnerabilities）。
 
    :return: 可用表名列表；无表或异常时返回中文说明
    """
    monitor.report_tool(tool_name="资产漏洞库-表名枚举：list_sql_tables", args={})
    config = get_db_config()
    try:
        # with 语句确保连接与游标自动关闭，避免连接泄漏
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                if not tables:
                    return "当前漏洞台账库中没有可用的表"
                table_names = [t[0] for t in tables]
                return f"可用的表有：{', '.join(table_names)}"
    except Error as e:
        return f"查询表名异常：{_format_mysql_error(e, config)}"


@tool
def get_table_data(
    table_name: Annotated[str, "要预览的资产或漏洞表名，如 company_assets、asset_vulnerabilities"],
) -> str:
    """
    读取指定资产/漏洞表的前 100 行数据（CSV 格式），用于了解字段结构与样例数据。
    调用前应先通过 list_sql_tables 确认表名存在。
    表名会经过安全清洗（剥离反引号、分号等危险字符）。

    :param table_name: 表名
    :return: 首行为列名、后续为数据行，逗号分隔；最多 100 行
    """
    monitor.report_tool(
        tool_name="资产漏洞库-表数据预览：get_table_data",
        args={"table_name": table_name},
    )
    config = get_db_config()
    try:
        safe_name = _sanitize_table_name(table_name)
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `{safe_name}` LIMIT 100")
                description = cursor.description
                if not description:
                    return f"表 {safe_name} 无数据或不存在"
                columns = [desc[0] for desc in description]
                rows = cursor.fetchall()
                return _rows_to_csv(columns, rows)
    except ValueError as e:
        return f"表名校验失败：{str(e)}"
    except Error as e:
        return f"查询表数据异常：{_format_mysql_error(e, config)}"


@tool
def execute_sql_query(
    query: Annotated[str, "针对资产表、漏洞表的 SELECT 语句，可含 JOIN/WHERE/聚合"],
) -> str:
    """
    执行自定义 SQL 查询，精确定位未修复高危漏洞、互联网暴露资产等。
    建议流程：list_sql_tables → get_table_data（了解字段）→ execute_sql_query。
    仅支持查询类语句；结果以 CSV 格式返回，最多 100 行。

    :param query: 完整 SELECT 语句
    :return: CSV 格式查询结果或异常说明
    """
    monitor.report_tool(
        tool_name="资产漏洞库-自定义查询：execute_sql_query",
        args={"query": query},
    )
    normalized = query.strip().upper()
    if not normalized.startswith("SELECT"):
        return "安全限制：仅允许执行 SELECT 查询语句"
    if ";" in query.rstrip().rstrip(";"):
        return "安全限制：不允许在单条语句中包含多个 SQL 分句"

    config = get_db_config()
    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                limited_query = query if "LIMIT" in normalized else f"{query.rstrip(';')} LIMIT 100"
                cursor.execute(limited_query)
                description = cursor.description
                if not description:
                    return f"SQL 执行成功但无结果集，语句：{query}"
                columns = [desc[0] for desc in description]
                rows = cursor.fetchall()
                return _rows_to_csv(columns, rows)
    except Error as e:
        return f"执行 SQL 异常：{_format_mysql_error(e, config)}"
