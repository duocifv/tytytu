# chains/coordination_chain.py
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from services.llm_service import llm  # Gemini instance

def run_coordination_chain(input_text: str) -> Dict[str, Any]:
    """
    Node 3: Trung tâm (PM + CSKH)
    - Lập kế hoạch, timeline
    - Phân công công việc
    - Báo cáo & giữ liên lạc KH

    Trả về dict: {"result_chain1", "result_chain2", "final_result"}
    """

    # 1️⃣ Tạo prompt templates
    p1 = ChatPromptTemplate.from_template(
        "Bạn là PM. Dựa trên input: {input_text}\n\n"
        "Hãy lập kế hoạch chi tiết và timeline (liệt kê các mốc chính, duration từng mốc)."
    )
    p2 = ChatPromptTemplate.from_template(
        "Dựa trên kế hoạch sau: {result_chain1}\n\n"
        "Hãy phân công công việc cho từng vai trò/nhân sự (mỗi nhiệm vụ ngắn gọn, ai chịu trách nhiệm)."
    )
    p3 = ChatPromptTemplate.from_template(
        "Dựa trên phân công công việc: {result_chain2}\n\n"
        "Tạo báo cáo tổng hợp (summary) để gửi khách hàng và hướng dẫn giữ liên lạc (1-2 câu hành động)."
    )

    # 2️⃣ Tạo chain chuẩn LangChain 2025 với RunnableLambda để feed dict
    chain3 = (
        p1 | llm
        | RunnableLambda(lambda result_chain1: {"result_chain1": result_chain1}) | p2 | llm
        | RunnableLambda(lambda result_chain2: {"result_chain2": result_chain2}) | p3 | llm
    )

    # 3️⃣ Invoke chain với input_text
    final_result = chain3.invoke({"input_text": input_text})

    # 4️⃣ Log thông tin
    print("   ├─ 📅 Lập kế hoạch, timeline")
    print("   ├─ 👥 Phân công công việc")
    print("   └─ 📢 Báo cáo & giữ liên lạc KH")

    return final_result
