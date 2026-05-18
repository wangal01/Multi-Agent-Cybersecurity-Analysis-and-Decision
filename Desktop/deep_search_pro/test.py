"""
本地快速测试大模型连通性。

常见报错 FileNotFoundError + SSL_CERT_FILE：
  conda 环境里 SSL_CERT_FILE 指向了不存在的证书路径，下面会自动修复。
"""
import os
import sys
from pathlib import Path

# 修复 conda 无效 SSL 证书路径（否则 httpx/openai 初始化失败）
for _var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
    _path = os.environ.get(_var)
    if _path and not Path(_path).is_file():
        os.environ.pop(_var, None)

try:
    import certifi

    os.environ["SSL_CERT_FILE"] = certifi.where()
except ImportError:
    pass

from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(find_dotenv())

api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_BASE_URL")
model_name = os.getenv("LLM_QWEN_MAX", "deepseek-chat")

if not api_key:
    print("错误: .env 中未配置 OPENAI_API_KEY")
    sys.exit(1)

print(f"模型: {model_name}")
print(f"API: {api_base}")

model = ChatOpenAI(
    model=model_name,
    openai_api_key=api_key,
    openai_api_base=api_base,
    temperature=0.7,
)

response = model.invoke("你好，请用一句话介绍你自己。")
print("\n回复:", response.content)
