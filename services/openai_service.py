import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI  # import OpenAI LLM

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Thiếu OPENAI_API_KEY trong .env")

# Khởi tạo model OpenAI
llm = ChatOpenAI(
    model="gpt-4o-mini",   # model free/giá rẻ, bạn có thể đổi thành gpt-4o
    api_key=api_key,
    temperature=0.7
)

# Test gọi LLM
resp = llm.invoke("Xin chào, bạn có khỏe không?")
print(resp.content)
