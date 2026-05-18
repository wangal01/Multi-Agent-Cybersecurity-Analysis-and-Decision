# 目标：加载 prompt/prompts.yml 中的提示词，供创建主智能体与三个子智能体使用
import yaml
from pathlib import Path

# 项目根目录：agent/ 的上一级
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PROMPTS_FILE = _PROJECT_ROOT / "prompt" / "prompts.yml"


def load_yaml(file_path: Path) -> dict:
    """
    加载指定位置的 yaml 配置文件。
    :param file_path: 配置文件路径
    :return: 解析后的字典
    """
    with open(file_path, "r", encoding="utf-8") as f:
        # safe_load 只解析数据，不会执行 yaml 内嵌的可执行对象（比 load 更安全）
        return yaml.safe_load(f)


# 模块导入时即加载配置（供 main_agent 与各 subagent 模块直接引用）
_prompt_yaml = load_yaml(_PROMPTS_FILE)

# 总指挥（main_agent）的系统提示词
main_agent_content = _prompt_yaml["main_agent"]

# 三个子智能体：database_query_agent / network_search_agent / knowledge_base_agent
sub_agents_content = _prompt_yaml["sub_agents"]
