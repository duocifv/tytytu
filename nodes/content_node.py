from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from services.llm_service import llm  # hoặc Groq wrapper tương ứng
from typing import List
import json
import traceback

# 1️⃣ Model JSON chuẩn (theo yêu cầu: 4 trường string)
class ContentOutput(BaseModel):
    caption: str
    short_post: str

# 2️⃣ Helper parse an toàn
def safe_parse(parser, text: str):
    try:
        return parser.parse(text)
    except Exception as e:
        # Log lỗi để debugging nếu cần
        traceback.print_exc()
        return ContentOutput(
            caption="Fallback caption",
            short_post="Fallback short post",
            creative_post="Fallback creative post",
            hidden_details="Fallback hidden details"
        )

# 3️⃣ Node content tối giản với prompt mới
def content_node(state):
    record = state.get("daily", {})
    # Chuẩn bị JSON input để model đọc (dán nguyên state)
    state_json = json.dumps(record, ensure_ascii=False, indent=2)

    parser = PydanticOutputParser(pydantic_object=ContentOutput)

    # Prompt (dán nguyên prompt template bạn muốn dùng)
    prompt_text = f"""
        Bạn là một biên tập viên mạng xã hội ngắn gọn, đồng cảm.
        Dữ liệu đầu vào: JSON dưới đây chứa thông tin hệ thống (thiên văn, địa lý, tin tức, phân tích).

        JSON_INPUT:
        {state_json}

        Nhiệm vụ:
        1. Phân tích JSON và rút ra thông điệp quan trọng nhất hôm nay cho công chúng 
        (an toàn + phục hồi thực tế + gợi ý tinh thần + nhắc nhở tài chính/công việc đơn giản).
        2. KHÔNG nhắc đến "Kinh Dịch", "quẻ", hay bất kỳ thuật ngữ huyền học. 
        KHÔNG hiển thị chỉ số kỹ thuật thô (Kp-index, độ Richter, ...). 
        Bạn có thể dùng thông tin này để định hướng giọng điệu và lời khuyên.
        3. Xuất ra JSON hợp lệ gồm 4 trường string:
        - "caption": 1 dòng ngắn, giàu cảm xúc, dễ đọc trên di động (≤ 80 ký tự, có thể có 1–2 emoji).
        - "short_post": 2–4 câu thực tế + an ủi, kết thúc bằng 1 CTA đơn giản 
            (VD: "Kiểm tra người già quanh nhà"). Giới hạn ~280 ký tự.

        Quy tắc văn phong:
        - Ngôn ngữ: tiếng Việt, tự nhiên, gần gũi, như người hàng xóm thân thiết nhắn tin.
        - Tránh từ chuyên môn phức tạp.
        - Nhấn mạnh: nghỉ ngơi, sửa chữa nhỏ, tiết kiệm vừa phải, quan tâm người yếu thế, 1 hành động nhỏ ngay hôm nay.
        - Giữ ngắn gọn, dễ đọc.

        Yêu cầu đầu ra:
        - Trả về JSON hợp lệ duy nhất, có 4 trường: caption, short_post, creative_post, hidden_details.
        - Không thêm chú thích, không thêm văn bản ngoài JSON.
        {parser.get_format_instructions()}
        """

    # Gọi LLM
    llm_output = llm.invoke(prompt_text)
    raw_result = llm_output.content if hasattr(llm_output, "content") else str(llm_output)

    # Parse JSON an toàn
    result = safe_parse(parser, raw_result)

    # Trả về dạng dict để downstream node dễ dùng
    print("📌 4 - content_node - ok")
    msg = HumanMessage(content=f"content_node generated social post for topic ")
    return {
        "status": "done",
        "messages": [msg],
        "outputs": result.model_dump()
    }
