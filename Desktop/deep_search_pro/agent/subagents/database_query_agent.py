# 子智能体：资产与漏洞台账 SQL 查询（MySQL）
from agent.prompts import sub_agents_content
from tools.mysql_tools import execute_sql_query, get_table_data, list_sql_tables

database_query_agent = {
    "name": sub_agents_content["database_query_agent"]["name"],
    "description": sub_agents_content["database_query_agent"]["description"],
    "system_prompt": sub_agents_content["database_query_agent"]["system_prompt"],
    "tools": [list_sql_tables, get_table_data, execute_sql_query],
}
