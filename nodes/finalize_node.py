# nodes2/log_node.py
from langchain_core.messages import HumanMessage
from brain.notion_logger import create_blog_log
from brain.telegram_notifier import notify_blog_published
from typing import Any


def list_to_text(data: Any) -> str:
    """Nếu là list thì join thành text, nếu là dict thì dump, còn lại cast str"""
    if not data:
        return ""
    if isinstance(data, list):
        return "\n".join([f"- {item}" for item in data])
    elif isinstance(data, dict):
        return "\n".join([f"{k}: {v}" for k, v in data.items()])
    return str(data)


def finalize_node(state: dict) -> dict:
    messages = []
    print(f"🔹 Finalize node state dump:", state)

    # Defaults
    published = False
    title_text = "Untitled"
    title_description = ""
    content_text = ""
    tags_text = ""

    try:
        topic = state.get("topic", "")
        outputs = state.get("outputs", {})

        # --- Keyword ---
        keyword_data = outputs.get("keyword", {})
        if hasattr(keyword_data, "keywords"):
            keyword_text = list_to_text(keyword_data.keywords)
        else:
            keyword_text = list_to_text(keyword_data)

        # --- Research ---
        research_data = outputs.get("research", {})
        if hasattr(research_data, "sources"):
            research_text = list_to_text([f"{s['title']} ({s['url']})" for s in research_data.sources])
        else:
            research_text = list_to_text(research_data)

        # --- Idea ---
        idea_data = outputs.get("idea", [])
        idea_text = list_to_text(idea_data)

        # --- Insight ---
        insight_data = outputs.get("insight", [])
        insight_text = list_to_text(insight_data)

        # --- Title & Description ---
        title_info = outputs.get("title")
        if title_info:
            if hasattr(title_info, "text"):
                title_text = title_info.text
            if hasattr(title_info, "description"):
                title_description = title_info.description

        # --- Content & Tags ---
        content_info = outputs.get("content")
        if content_info:
            if hasattr(content_info, "body"):
                content_text = content_info.body
            if hasattr(content_info, "tags"):
                tags_text = list_to_text(content_info.tags)

        # --- Publish status ---
        publish_data = outputs.get("publish", {})
        published = False
        if isinstance(publish_data, dict):
            published = publish_data.get("publish", {}).get("done", False)

        print(f"publish_data--------------->", publish_data)

        # --- Lưu vào Notion ---
        create_blog_log(
            task_name=title_text,
            description=title_description,
            topic=topic,
            audience=insight_text,
            guideline=research_text,
            keywords=keyword_text,
            outline=idea_text,
            facts=insight_text,
            content=content_text,
            tags=tags_text,
            status="Hoàn thành" if published else "Draft",
        )
        print("✅ Đã gửi dữ liệu lên Notion")
        messages.append(HumanMessage(content="✅ Blog saved to Notion"))

    except Exception as e:
        msg = f"❌ Failed to save Notion: {e}"
        print(msg)
        messages.append(HumanMessage(content=msg))

    # --- Gửi Telegram nếu published ---
    try:
        if published:
            notify_blog_published(f"🚀 Notify: đã đăng facebook và website  '{title_text}'")
            messages.append(HumanMessage(content="✅ Sent Telegram notification"))
    except Exception as e:
        messages.append(HumanMessage(content=f"❌ Failed to notify Telegram: {e}"))

    return {
        "status": "done",
        "messages": messages,
    }
