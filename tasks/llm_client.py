import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Thiếu GOOGLE_API_KEY")

llm = init_chat_model(
    model="gemini-2.5-flash",
    model_provider="google_genai",
    api_key=api_key,
)
