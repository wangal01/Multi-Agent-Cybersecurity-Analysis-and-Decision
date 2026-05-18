"""
网络空间威胁情报与 OSINT 工具。
供 network_search_agent 检索在野利用情报、止损方案及 C2 威胁情报。
"""
import json
import os
from typing import Literal

import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from api.monitor import monitor

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

THREATFOX_API_URL = "https://threatfox-api.abuse.ch/api/v1/"

# 接口不可用时的静态仿真保底（便于联调与演示）
_STATIC_C2_FALLBACK: dict[str, dict] = {
    "203.0.113.88": {
        "query_status": "ok",
        "data": [
            {
                "malware": "CobaltStrike",
                "malware_printable": "Cobalt Strike",
                "confidence_level": 90,
                "threat_type": "botnet_cc",
                "tags": ["cobalt_strike", "apt_simulation"],
            }
        ],
        "note": "静态仿真数据（ThreatFox 接口不可达时启用）",
    },
}


def _format_threatfox_hit(ip_address: str, payload: dict) -> str:
    records = payload.get("data") or []
    lines = [
        f"【C2 威胁情报命中】目标 IP：{ip_address}",
        f"数据源：abuse.ch ThreatFox（query_status={payload.get('query_status', 'ok')}）",
    ]
    if payload.get("note"):
        lines.append(f"说明：{payload['note']}")
    for idx, item in enumerate(records, 1):
        lines.append(
            f"  [{idx}] 恶意软件家族：{item.get('malware_printable') or item.get('malware', '未知')}；"
            f"威胁类型：{item.get('threat_type', '未知')}；"
            f"可信度得分：{item.get('confidence_level', 'N/A')}；"
            f"标签：{', '.join(item.get('tags') or [])}"
        )
    return "\n".join(lines)


def _format_threatfox_miss(ip_address: str, query_status: str) -> str:
    return (
        f"【C2 威胁情报未命中】目标 IP：{ip_address}\n"
        f"ThreatFox query_status：{query_status}\n"
        f"结论：该 IP 未在 ThreatFox 全球恶意 C2 库中登记为已知 C2 伺服器（不代表绝对安全）。"
    )


@tool
def internet_search(
    query: Annotated[str, "检索关键词，如 CVE 编号、漏洞在野利用、临时止损方案"],
    topic: Annotated[
        Literal["news", "finance", "general"],
        "检索主题类型：news 新闻、finance 金融、general 综合",
    ] = "general",
    max_results: Annotated[int, "返回结果条数上限"] = 5,
    include_raw_content: Annotated[bool, "是否返回网页原文（更详细但更耗 token）"] = False,
):
    """
    基于 Tavily 的互联网公开情报检索。
    用于查询漏洞在野利用变种、厂商公告、临时修复与止损方案等外网 OSINT 信息。
    不用于查询企业内部资产台账或 RAG 合规库。
    """
    monitor.report_tool(
        tool_name="网络空间情报-互联网检索：internet_search",
        args={
            "query": query,
            "topic": topic,
            "max_results": max_results,
            "include_raw_content": include_raw_content,
        },
    )
    return tavily_client.search(
        query=query,
        topic=topic,
        max_results=max_results,
        include_raw_content=include_raw_content,
    )


@tool
def check_c2_threat_intelligence(
    ip_address: Annotated[str, "待检测的服务器 IP 地址（公网或内网映射出口 IP）"],
) -> str:
    """
    查询 abuse.ch ThreatFox 全球恶意 C2 数据库（免 Key）。
    若 IP 被标记为 C2 伺服器，返回恶意软件家族、威胁类型与可信度得分；否则返回未命中说明。
    接口异常时启用静态仿真保底策略。
    """
    monitor.report_tool(
        tool_name="网络空间情报-C2检测：check_c2_threat_intelligence",
        args={"ip_address": ip_address},
    )
    ip = ip_address.strip()
    payload_body = {"query": "search_ioc", "search_term": ip}

    try:
        response = requests.post(
            THREATFOX_API_URL,
            json=payload_body,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()
        query_status = result.get("query_status", "unknown")

        if query_status == "ok" and result.get("data"):
            return _format_threatfox_hit(ip, result)
        if query_status in ("no_result", "not_found"):
            return _format_threatfox_miss(ip, query_status)
        return _format_threatfox_miss(ip, query_status)

    except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
        fallback = _STATIC_C2_FALLBACK.get(ip)
        if fallback:
            return _format_threatfox_hit(ip, fallback)
        return (
            f"【C2 威胁情报查询异常】IP：{ip}；错误：{str(e)}\n"
            f"已尝试静态仿真库，该 IP 无预置记录。\n"
            f"建议：稍后重试 ThreatFox，或结合 internet_search 检索该 IP 的公开威胁报告。"
        )
