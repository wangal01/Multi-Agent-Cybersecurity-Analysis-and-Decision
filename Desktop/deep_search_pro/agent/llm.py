from dotenv import load_dotenv, find_dotenv
import os
from langchain.chat_models import init_chat_model

# 加载配置文件；find_dotenv() 从项目目录向上查找 .env
load_dotenv(find_dotenv())

model = init_chat_model(
    model=os.getenv("LLM_QWEN_MAX"),
    model_provider="openai",
)

