# 子智能体：网络空间 OSINT + ThreatFox C2 情报
from agent.prompts import sub_agents_content
from tools.security_osint_tools import check_c2_threat_intelligence, internet_search

network_search_agent = {
    "name": sub_agents_content["network_search_agent"]["name"],
    "description": sub_agents_content["network_search_agent"]["description"],
    "system_prompt": sub_agents_content["network_search_agent"]["system_prompt"],
    "tools": [internet_search, check_c2_threat_intelligence],
}
