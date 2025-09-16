# chains/translation_chain.py
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from services.llm_service import llm  # Gemini instance

def run_translation_chain(input_text: str) -> Dict[str, Any]:
    """
    Node 2: Thông dịch
    - Dịch ngôn ngữ khách → kỹ thuật
    - Chuẩn hóa thuật ngữ
    - Tạo brief chuẩn
    """

    # 1️⃣ Tạo prompt templates
    p1 = ChatPromptTemplate.from_template(
        "Bạn là trợ lý kỹ thuật. Dịch nội dung sau sang ngôn ngữ kỹ thuật: {input_text}"
    )
    p2 = ChatPromptTemplate.from_template(
        "Dựa trên nội dung sau: {step1_translate}, hãy chuẩn hóa thuật ngữ chuyên ngành."
    )
    p3 = ChatPromptTemplate.from_template(
        "Dựa trên nội dung đã chuẩn hóa: {step2_normalize}, tạo một brief ngắn gọn, chuẩn."
    )

    # 2️⃣ Tạo chain chuẩn LangChain 2025 với RunnableLambda để feed dict
    chain3 = (
        p1 | llm
        | RunnableLambda(lambda step1_translate: {"step1_translate": step1_translate}) | p2 | llm
        | RunnableLambda(lambda step2_normalize: {"step2_normalize": step2_normalize}) | p3 | llm
    )

    # 3️⃣ Invoke chain với input_text
    final_result = chain3.invoke({"input_text": input_text})

    # 4️⃣ Log thông tin
    print("   ├─ 🌐 Dịch ngôn ngữ khách → kỹ thuật")
    print("   ├─ 📖 Chuẩn hóa thuật ngữ")
    print("   └─ 📝 Tạo brief chuẩn")

    return final_result
