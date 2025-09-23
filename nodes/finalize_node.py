# nodes2/log_node.py
from langchain_core.messages import HumanMessage
from brain.notion_logger import create_blog_log
from brain.telegram_notifier import notify_blog_published


def list_to_text(data):
    """Nếu là list thì join thành text, nếu là dict thì dump, còn lại cast str"""
    if not data:
        return ""
    if isinstance(data, list):
        return "\n".join([f"- {item}" for item in data])
    elif isinstance(data, dict):
        return "\n".join([f"{k}: {v}" for k, v in data.items()])
    return str(data)


def finalize_node(state):
    messages = []
    print("🔹 Finalize node state dump:")

    # Khởi tạo mặc định để tránh lỗi UnboundLocalError
    published = True
    url = ""
    title_text = "Untitled"

    try:
        topic = state.get("topic", "")
        outputs = state.get("outputs", {})

        # --- Convert từng trường thành text ---
        # Keyword
        keyword_data = outputs.get("keyword", [])
        keyword_text = list_to_text(keyword_data)

        # Research
        research_data = outputs.get("research", [])
        research_text = list_to_text(research_data)

        # Idea
        idea_data = outputs.get("idea", [])
        idea_text = list_to_text(idea_data)

        # Insight
        insight_data = outputs.get("insight", [])
        insight_text = list_to_text(insight_data)

        # Title & Description
        title_info = outputs.get("title", "")
        if isinstance(title_info, dict):
            title_text = str(title_info.get("text", "")) or "Untitled"
            title_description = str(title_info.get("description", ""))
        else:
            title_text = str(title_info) or "Untitled"
            title_description = ""

        # Content & Tags
        content_info = outputs.get("content", "")
        if isinstance(content_info, dict):
            content_text = str(content_info.get("body", ""))
            tags_text = list_to_text(content_info.get("tags", []))
        else:
            content_text = str(content_info)
            tags_text = ""

        # Publish status
        publish_data = outputs.get("publish", {})
        if isinstance(publish_data, dict):
            published = publish_data.get("published", False)
            # url = publish_data.get("url", "")
        else:
            published = True
            # url = ""
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
    if published:
        try:
            # notify_blog_published(f"🚀 Notify: Published '{title_text}' ")
            messages.append(HumanMessage(content="✅ Sent Telegram notification"))
        except Exception as e:
            messages.append(HumanMessage(content=f"❌ Failed to notify Telegram: {e}"))

    notify_blog_published(f"🚀 Notify: đã đăng facebook và website  ")
    return {
        "status": "done",
        "messages": messages,
    }
