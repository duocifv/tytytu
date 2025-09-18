import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from tools2.content_length_tool import content_length_tool
from tools2.word_count_tool import word_count_tool

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Thiếu GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    model_provider="google_genai",
    api_key=api_key,
)

llm_tools = llm.bind_tools([content_length_tool, word_count_tool])
