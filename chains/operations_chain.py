# chains/operations_chain.py
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from services.llm_service import llm  # Gemini instance

def run_operations_chain(request: str) -> Dict[str, Any]:
    """
    Chain 4 bước:
    1️⃣ Tóm tắt request
    2️⃣ Phân rã các nhu cầu
    3️⃣ Xác định mục tiêu, phạm vi, deadline
    4️⃣ Tổng hợp cho chuyển giao
    """

    # 1️⃣ Tạo prompt templates
    p1 = ChatPromptTemplate.from_template(
        "Bạn là trợ lý. Tóm tắt: {request}"
    )
    p2 = ChatPromptTemplate.from_template(
        "Dựa trên: {result_chain1}, phân rã các nhu cầu."
    )
    p3 = ChatPromptTemplate.from_template(
        "Dựa trên: {result_chain2}, xác định mục tiêu, phạm vi, deadline."
    )
    p4 = ChatPromptTemplate.from_template(
        "Tổng hợp cho chuyển giao: {result_chain3}"
    )

    # 2️⃣ Tạo chain chuẩn LangChain 2025 với RunnableLambda để feed dict
    chain4 = (
        p1 | llm
        | RunnableLambda(lambda result_chain1: {"result_chain1": result_chain1}) | p2 | llm
        | RunnableLambda(lambda result_chain2: {"result_chain2": result_chain2}) | p3 | llm
        | RunnableLambda(lambda result_chain3: {"result_chain3": result_chain3}) | p4 | llm
    )

    # 3️⃣ Invoke chain với request
    final_result = chain4.invoke({"request": request})

    return final_result
