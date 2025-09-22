import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tools2.content_length_tool import content_length_tool
from tools2.word_count_tool import word_count_tool

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Thiếu OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-4o-mini",  # miễn phí
    api_key=api_key,
)

llm_tools = llm.bind_tools([content_length_tool, word_count_tool])
