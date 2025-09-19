# notion_logger.py
from services.notion_service import NotionService

notion = NotionService()

def not_started_log(node_name: str):
    """
    Node chưa chạy → "Chưa làm"
    """
    try:
        notion.update_task(node_name, {"Status": {"status": {"name": "Chưa làm"}}})
    except Exception as e:
        print("⚠️ Lỗi not_started_log node:", e)

def start_log(node_name: str):
    """
    Node vừa bắt đầu → "Bắt đầu"
    """
    try:
        notion.update_task(node_name, {"Status": {"status": {"name": "Đang làm"}}})
    except Exception as e:
        print("⚠️ Lỗi start_log node:", e)

def doing_log(node_name: str):
    """
    Node đang chạy → "Đang làm"
    """
    try:
        notion.update_task(node_name, {"Status": {"status": {"name": "Đang làm"}}})
    except Exception as e:
        print("⚠️ Lỗi doing_log node:", e)

def done_log(node_name: str):
    """
    Node hoàn thành → "Hoàn thành"
    """
    try:
        notion.update_task(node_name, {"Status": {"status": {"name": "Hoàn thành"}}})
    except Exception as e:
        print("⚠️ Lỗi done_log node:", e)

def failed_log(node_name: str):
    """
    Node lỗi → "Bị lỗi"
    """
    try:
        notion.update_task(node_name, {"Status": {"status": {"name": "Bị lỗi"}}})
    except Exception as e:
        print("⚠️ Lỗi failed_log node:", e)


def create_blog_log(
    task_name: str,
    topic: str = "",
    audience: str = "",
    guideline: str = "",
    keywords: str = "",
    outline: str = "",
    facts: str = "",
    content: str = "",
    images: str = "",
    video: str = "",
    status: str = "Đang làm",
):
    """
    📌 Tạo mới một blog trong Notion (Kanban Blog Database).
    """
    try:
        notion.update_blog(task_name,{
                "Topic": {"rich_text": [{"text": {"content": topic}}]},
                "Audience": {"rich_text": [{"text": {"content": audience}}]},
                "Guideline": {"rich_text": [{"text": {"content": guideline}}]},
                "Keywords": {"rich_text": [{"text": {"content": keywords}}]},
                "Outline": {"rich_text": [{"text": {"content": outline}}]},
                "Facts": {"rich_text": [{"text": {"content": facts}}]},
                "Content": {"rich_text": [{"text": {"content": content}}]},
                "Images": {"rich_text": [{"text": {"content": images}}]},
                "Video": {"rich_text": [{"text": {"content": video}}]},
                "Status": {"select": {"name": status}},
            })
    except Exception as e:
        print("⚠️ Lỗi create_blog_log:", e)