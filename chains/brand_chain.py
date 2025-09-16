# chains/brand_chain.py
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from services.llm_service import llm  # Gemini instance

def run_brand_chain(input_text: str) -> Dict[str, Any]:
    """
    Node 4: Quản trị Thương hiệu
    - Kiểm tra tone, hình ảnh
    - Đối chiếu guideline
    - Duyệt ý tưởng ban đầu
    """

    # 1️⃣ Tạo prompt templates
    p1 = ChatPromptTemplate.from_template(
        "Dựa trên nội dung: {input_text}, kiểm tra tone và hình ảnh có phù hợp không."
    )
    p2 = ChatPromptTemplate.from_template(
        "Dựa trên kết quả kiểm tra tone/hình ảnh: {step1_tone}, đối chiếu với guideline của thương hiệu."
    )
    p3 = ChatPromptTemplate.from_template(
        "Dựa trên đối chiếu guideline: {step2_guideline}, duyệt ý tưởng ban đầu và tổng hợp kết quả."
    )

    # 2️⃣ Tạo chain chuẩn LangChain 2025 với RunnableLambda để feed dict
    chain3 = (
        p1 | llm
        | RunnableLambda(lambda step1_tone: {"step1_tone": step1_tone}) | p2 | llm
        | RunnableLambda(lambda step2_guideline: {"step2_guideline": step2_guideline}) | p3 | llm
    )

    # 3️⃣ Invoke chain với input_text
    final_result = chain3.invoke({"input_text": input_text})

    # 4️⃣ Log thông tin
    print("   ├─ 🎨 Kiểm tra tone, hình ảnh")
    print("   ├─ 📚 Đối chiếu guideline")
    print("   └─ ✅ Duyệt ý tưởng ban đầu")

    return final_result
