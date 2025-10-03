# main_pipeline_with_two_tier.py
import os
from typing import TypedDict
import uuid
import traceback
import random
from io import BytesIO
import requests
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from PIL import Image as PILImage
from brain.notion_logger import get_hexagram_log
from services.generate_video_service import generate_video
from services.llm_service import llm
from services.facebook_service import FacebookPipeline
from services.rag_service import RAGRetriever

# -----------------------------
# Thư mục lưu tạm
# -----------------------------
TEMP_DIR = "generated_images"
os.makedirs(TEMP_DIR, exist_ok=True)

# -----------------------------
# 1️⃣ Model JSON chuẩn
# -----------------------------
class ContentOutput(BaseModel):
    fb_title: str
    fb_description: str
    image_prompt: str
    daily_stoic_prompt: str
    daily_stoic: str
    quote_author: str
    poster_tone: str

def safe_parse(parser, text: str):
    try:
        return parser.parse(text)
    except Exception:
        traceback.print_exc()
        return ContentOutput(
            fb_title="Fallback Title",
            fb_description="Fallback description",
            image_prompt="city street rainy",
            daily_stoic="Fallback stoic",
            quote_author="Unknown",
            poster_tone="neutral"
        )

def extract_simple_notion(notion_raw: dict, keys=None):
    if keys is None:
        keys = ["Nhan", "Dia", "Thien", "Summary", "KeyEvent", "Health", "Work", "Effect", 
                "Trend", "Finance", "Psychology", "Family", "Spiritual", "Community"]
    simple = {}
    try:
        props = notion_raw.get("properties", {})
        for k in keys:
            v = props.get(k)
            if not v:
                continue
            rich_text = v.get("rich_text", [])
            if rich_text and isinstance(rich_text, list):
                simple[k] = " ".join(rt.get("plain_text", "") for rt in rich_text).strip()
    except Exception as e:
        print(e)
    return simple

# -----------------------------
# 2️⃣ Tạo ảnh từ Hugging Face Space
# -----------------------------
def generate_image_from_prompt(prompt: str) -> PILImage.Image | None:
    url = "https://duocifv-tytytu-image.hf.space/generate-image"
    payload = {"prompt": prompt}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=2000)
        response.raise_for_status()
        img = PILImage.open(BytesIO(response.content)).convert("RGB")
        print("✅ Image generated successfully")
        return img
    except Exception as e:
        print("❌ Lỗi tạo ảnh:", e)
        traceback.print_exc()
        return None

# -----------------------------
# Helper: đăng media lên Facebook
# -----------------------------
def post_media(pipeline: FacebookPipeline, video_path=None, image_path=None, fb_title="", fb_description=""):
    fb_title_safe = fb_title[:100]
    try:
        if video_path:
            fb_result = pipeline.post_video(video_path=video_path, title=fb_title_safe, description=fb_description)
            success = bool(fb_result.get("id"))
        elif image_path:
            fb_result = pipeline.run(image_path=image_path, title=fb_title, description=fb_description)
            success = bool(fb_result.get("published", False))
        else:
            success = False
    except Exception:
        traceback.print_exc()
        success = False
    return success

# -----------------------------
# 3️⃣ Semantic Randomization helpers
# -----------------------------
def paraphrase_text(text: str, style="friendly") -> str:
    """
    Sử dụng LLM để:
    - Viết lại nội dung hoàn toàn mới (paraphrase)
    - Giữ cùng ý tưởng
    - Chuyển sang tiếng Việt chuẩn, thân mật, gần gũi
    - Áp dụng style tùy chọn (ví dụ: friendly, witty, warm)
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Bạn là chuyên gia viết bài Facebook bằng tiếng Việt, thân mật, dí dỏm, gần gũi."),
        ("user", f"""
            Viết lại nội dung sau thành bài đăng hoàn toàn mới bằng **tiếng Việt**, giữ cùng ý tưởng nhưng cách diễn đạt khác, 
            style: {style}.

            Nội dung gốc (có thể là tiếng Anh): 
            {text}

            Chỉ trả về **nội dung bài đăng tiếng Việt**, không thêm chú thích hay giải thích.
        """)
    ])
    
    out = llm.invoke(prompt.format())
    return getattr(out, "content", text)

def randomize_image_prompt(prompt: str) -> str:
    """LLM sinh prompt hình ảnh khác dựa trên concept"""
    prompt_wrap = ChatPromptTemplate.from_messages([
        ("system", "You are an expert AI image prompt creator. Always reply in English."),
        ("user", f"""
            Concept: {prompt}
            Please write a completely new AI image prompt, different but keeping the same idea,
            concise (≤77 characters), in English, suitable for the context of a Facebook post.
            Return only the prompt text, no explanation.
        """)
    ])
    out = llm.invoke(prompt_wrap.format())
    new_prompt = getattr(out, "content", prompt)
    return new_prompt[:77]

# Định nghĩa schema JSON
class QuoteSchema(BaseModel):
    new_quote: str
    new_author: str

def randomize_daily_quote(prompt: str) -> tuple[str, str]:
    parser = PydanticOutputParser(pydantic_object=QuoteSchema)
    parser_instructions = parser.get_format_instructions()

    daily_stoic_template = ChatPromptTemplate.from_messages([
        ("system", "Bạn là chuyên gia viết câu triết lý, truyền năng lượng. Tập trung ngắn gọn, xúc tích."),
        ("user",
         "prompt: {prompt}\n"
         "Nhiệm vụ: Từ câu sau, tạo 1 câu mới DUY NHẤT (paraphrase) có cùng ý nghĩa và 1 tác giả biến thể AN TOÀN.\n\n"
         "Yêu cầu nghiêm ngặt: chỉ trả về JSON với các trường:\n"
         "{parser_instructions}\n"
         "- new_quote: câu triết lý paraphrase, giữ ý nghĩa và dịch sang tiếng việt.\n"
         "- new_author: tác giả biến thể an toàn (ví dụ 'Marcus Aurelius').\n"
         "Trả về chỉ JSON, không thêm gì khác.")
    ]).partial(parser_instructions=parser_instructions)

    prompt_content = daily_stoic_template.format(prompt=prompt)
    llm_output = llm.invoke(prompt_content)

    content_obj = safe_parse(parser, getattr(llm_output, "content", str(llm_output)))

    return content_obj.new_quote, content_obj.new_author  # Dùng .new_quote thay vì ["new_quote"]


# -----------------------------
# 4️⃣ Main pipeline
# -----------------------------
def content_and_facebook_node(state: dict):
    msg_list = []
    fb_success = False
    temp_image_path = None
    temp_video_path = None

    # 1️⃣ Lấy dữ liệu Notion
    notion_raw = get_hexagram_log()
    notion_data = extract_simple_notion(notion_raw)
    print("✅ Dữ liệu rút gọn từ Notion:", notion_data)
    if not notion_data:
        notion_data = {"Summary": "Không có dữ liệu hôm nay"}

    notion_data_str = str(notion_data)
    parser = PydanticOutputParser(pydantic_object=ContentOutput)

    # -----------------------------
    # 2️⃣ Tier 1: Phân tích dữ liệu
    # -----------------------------
    p_analysis = ChatPromptTemplate.from_messages([
        ("system", "Bạn là chuyên gia phân tích dữ liệu cộng đồng."),
        ("user",
         "Dữ liệu JSON từ Notion: {notion_data}\n"
         "Hãy phân tích và rút ra các insight chính:\n"
         "- Tình hình thiên tai, dịch bệnh, kinh tế, tâm lý\n"
         "- Tác động đến sức khỏe, công việc, đời sống gia đình\n"
         "- Gợi ý cách ứng phó, chăm sóc sức khỏe và tinh thần\n"
         "Trả về văn bản súc tích, dễ hiểu.")
    ]).partial(notion_data=notion_data_str)
    prompt_analysis = p_analysis.format(notion_data=notion_data_str)
    insight_text = getattr(llm.invoke(prompt_analysis), "content", "")
    
    # -----------------------------
    # 3️⃣ RAG: lấy dữ liệu thực tế
    # -----------------------------
    rag = RAGRetriever(sources=["VNExpress","Khí tượng Thủy văn","WHO"])
    rag_info = rag.retrieve(notion_data)
    if isinstance(rag_info, dict):
        rag_info = str(rag_info)

    # -----------------------------
    # 4️⃣ Tier 2: Viết content dựa trên insight + RAG
    # -----------------------------
    parser_instructions = parser.get_format_instructions()
    p_content = ChatPromptTemplate.from_messages([
    ("system", "You are a social media editor, writing casual, friendly Facebook posts."),
    ("user", """
        Based on the analysis insights: {insight}
        And real-world data from RAG: {rag_info}

        Write a casual, friendly, and useful Facebook post, like a friend talking to the community.

        Requirements:
        - Opening: describe a concrete life scene (e.g., empty café, child coughing, motorbike stalled in rain…)
        - Body:
        + Everyday + informative: integrate real-world data influence.
        + Practical advice: health, safety, daily life tips.
        + Community angle: mention sharing and helping each other.
        - Ending: warm, witty, gentle tone, like giving advice to loved ones.
        - Daily Stoic: include a short, uplifting philosophical sentence.
        - Length: 150–250 words.
        - Style: friendly, emotional, balancing concern and hope.
        - Optional: one hashtag at the end.
        - Do not use academic language, dry lists, or technical data.

        Output: JSON with 6 fields:
        - fb_title (50–100 characters)
        - fb_description (≤500 characters)
        - image_prompt: short (≤77 characters), accurately describing the opening image, contextually relevant.
        - daily_stoic_prompt: short, concise, uplifting philosophical sentence suitable for the post, in English.
        - poster_tone (choose from: ["happy","sad","neutral","vibrant","warm","cool","pastel","bold","calm","dark","light","luxury","natural"])

        Only output correctly formatted JSON. Do not add any extra text.

        Schema: {parser_instructions}
        """)
        ]).partial(parser_instructions=parser_instructions)


    prompt_content = p_content.format(insight=insight_text, rag_info=rag_info,parser_instructions=parser_instructions)
    llm_output = llm.invoke(prompt_content)
    content_obj = safe_parse(parser, getattr(llm_output, "content", str(llm_output)))

    # 5️⃣ Semantic randomization
    content_obj.fb_description = paraphrase_text(content_obj.fb_description)
    content_obj.daily_stoic, content_obj.quote_author = randomize_daily_quote(
        content_obj.daily_stoic_prompt
    )
    content_obj.image_prompt = randomize_image_prompt(content_obj.image_prompt)

    print("📌 Content JSON sau randomization:", content_obj)

    # 6️⃣ Tạo ảnh + video
    if content_obj.image_prompt:
        pil_img = generate_image_from_prompt(content_obj.image_prompt)
        if pil_img:
            temp_image_path = os.path.join(TEMP_DIR, f"v_{uuid.uuid4().hex[:4]}.jpg")
            try:
                pil_img.save(temp_image_path, format="JPEG", quality=95)
            except Exception:
                traceback.print_exc()
                temp_image_path = None

            if temp_image_path:
                temp_video_path = os.path.join(TEMP_DIR, f"v_{uuid.uuid4().hex[:4]}.mp4")
                try:
                    generate_video(
                        temp_image_path,
                        content_obj.daily_stoic or content_obj.fb_description,
                        content_obj.quote_author or None,
                        output=temp_video_path,
                        size=(1080,1350),
                        total_frames=180,
                        fps=30
                    )
                    if not os.path.exists(temp_video_path):
                        temp_video_path = None
                except Exception:
                    traceback.print_exc()
                    temp_video_path = None
            msg_list.append(HumanMessage(content="✅ Video created" if temp_video_path else "❌ Video creation failed"))
        else:
            msg_list.append(HumanMessage(content="❌ Image generation failed"))

    # 7️⃣ Đăng FB
    if temp_video_path or temp_image_path:
        pipeline = FacebookPipeline()
        fb_success = post_media(
            pipeline,
            video_path=temp_video_path,
            image_path=temp_image_path,
            fb_title=content_obj.fb_title,
            fb_description=content_obj.fb_description
        )
        msg_list.append(HumanMessage(content=f"Facebook: {'✅ Published' if fb_success else '❌ Failed'}"))

    # 8️⃣ Cleanup temp
    for path in [temp_image_path, temp_video_path]:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            traceback.print_exc()

    return {"status": "done", "messages": msg_list, "published": fb_success}
