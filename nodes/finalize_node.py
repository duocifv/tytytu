# nodes2/log_node.py
from langchain_core.messages import HumanMessage
from brain.notion_logger import create_blog_log
from brain.telegram_notifier import notify_blog_published

def finalize_node(state):
    messages = []

    # --- Print toàn bộ state để debug ---
    print("🔹 Finalize node state dump:")
    print(state)

    # --- Lưu Notion ---
    try:
        results = state.get("results", {})
        outputs = results.get("outputs", {})

        # Lấy các trường từ state
        task_name = outputs.get("title", {}).get("title", "Untitled Blog")
        
        keyword_list = outputs.get("keyword", {}).get("keywords", [])
        keywords = ", ".join(keyword_list) if keyword_list else ""

        # Giới hạn content để tránh lỗi Notion (rich_text ≤ 2000 ký tự)
        full_content = outputs.get("content", {}).get("content", "")
        MAX_LENGTH = 2000
        content = full_content[:MAX_LENGTH]

        image_list = outputs.get("image", {}).get("image_urls", [])
        images = ", ".join(image_list) if image_list else ""

        published = outputs.get("publish", {}).get("published", False)

        # Gọi hàm tạo blog log
        create_blog_log(
            task_name=task_name,
            keywords=keywords,
            content=content,
            images=images,
            status="Hoàn thành" if published else "Draft"
        )

        print("✅ Đã gửi dữ liệu lên Notion")
        messages.append(HumanMessage(content="✅ Blog saved to Notion"))

    except Exception as e:
        msg = f"❌ Failed to save Notion: {e}"
        print(msg)
        messages.append(HumanMessage(content=msg))

    # --- Gửi Telegram ---
    try:
        title = state["status"].get("node_data", {}).get("title", {}).get("title", "")
        url = state["results"]["outputs"].get("publish", {}).get("url", "")

        # Gửi sang Facebook, Telegram, v.v...
        notify_blog_published(f"🚀 Notify: Published '{title}' at {url}")
        messages.append(HumanMessage(content="✅ Sent Telegram notification"))
    except Exception as e:
        messages.append(HumanMessage(content=f"❌ Failed to notify Telegram: {e}"))

    return {
        "status": "done",
        "messages": messages,
    }
