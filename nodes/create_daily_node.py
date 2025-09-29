from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from brain.types import FullDailyData
from services.llm_service import llm  # hoặc Groq wrapper
from typing import List
from services.daily_hexagram_service import DailyHexagramService

# 1️⃣ Model JSON chuẩn
class DailyOutput(BaseModel):
    status: str
    messages: str
    daily: FullDailyData


def create_daily_node(state):
    record = state.get("daily", {})
    print(f"create_daily_node state--------->", state)
    svc = DailyHexagramService()
    result = svc.create_daily_node(
        record.get("thien"),
        record.get("dia"),
        record.get("nhan"),
        record.get("key_event")
    )
    print("📌 2/create_daily_node output:", result)

    msg = HumanMessage(content="create_daily_node tạo quẻ")
    return {
        "status": "done",
        "messages": [msg],
        "daily": result
    }
