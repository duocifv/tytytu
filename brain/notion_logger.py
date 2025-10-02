# notion_logger.py
from services.notion_service import NotionService

notion = NotionService()

def not_started_log(node_name: str):
    """Node chưa chạy → 'Chưa làm'"""
    try:
        notion.update_task(node_name, {"Status": {"status": {"name": "Chưa làm"}}})
    except Exception as e:
        print("⚠️ Lỗi not_started_log node:", e)

def start_log(node_name: str):
    """Node vừa bắt đầu → 'Đang làm'"""
    try:
        notion.update_task(node_name, {"Status": {"status": {"name": "Đang làm"}}})
    except Exception as e:
        print("⚠️ Lỗi start_log node:", e)

def doing_log(node_name: str):
    """Node đang chạy → 'Đang làm'"""
    try:
        notion.update_task(node_name, {"Status": {"status": {"name": "Đang làm"}}})
    except Exception as e:
        print("⚠️ Lỗi doing_log node:", e)

def done_log(node_name: str):
    """Node hoàn thành → 'Hoàn thành'"""
    try:
        notion.update_task(node_name, {"Status": {"status": {"name": "Hoàn thành"}}})
    except Exception as e:
        print("⚠️ Lỗi done_log node:", e)

def failed_log(node_name: str):
    """Node lỗi → 'Bị lỗi'"""
    try:
        notion.update_task(node_name, {"Status": {"status": {"name": "Bị lỗi"}}})
    except Exception as e:
        print("⚠️ Lỗi failed_log node:", e)


def _safe_text(text: str, max_len: int = 1900) -> str:
    """Giới hạn độ dài rich_text để tránh lỗi Notion (>2000 ký tự)."""
    return text[:max_len] if text else ""


def create_blog_log(
    task_name: str,
    description: str = "",
    topic: str = "",
    audience: str = "",
    guideline: str = "",
    keywords: str = "",
    outline: str = "",
    facts: str = "",
    content: str = "",
    tags: str = "",
    images: str = "",
    video: str = "",
    status: str = "Đang làm",
):
    """
    📌 Tạo mới một blog trong Notion (Kanban Blog Database).
    """
    try:
        payload = {
            "Name": {"title": [{"text": {"content": _safe_text(task_name)}}]},
            "Description": {"rich_text": [{"text": {"content": _safe_text(description)}}]},
            "Topic": {"rich_text": [{"text": {"content": _safe_text(topic)}}]},
            "Audience": {"rich_text": [{"text": {"content": _safe_text(audience)}}]},
            "Guideline": {"rich_text": [{"text": {"content": _safe_text(guideline)}}]},
            "Keywords": {"rich_text": [{"text": {"content": _safe_text(keywords)}}]},
            "Outline": {"rich_text": [{"text": {"content": _safe_text(outline)}}]},
            "Facts": {"rich_text": [{"text": {"content": _safe_text(facts)}}]},
            "Content": {"rich_text": [{"text": {"content": _safe_text(content, 1900)}}]},
            "Images": {"rich_text": [{"text": {"content": _safe_text(images)}}]},
            "Video": {"rich_text": [{"text": {"content": _safe_text(video)}}]},
            "Tags": {"multi_select": [{"name": t.strip()} for t in tags.split(",") if t.strip()]},
            "Status": {"select": {"name": status}},
        }

        res = notion.update_blog(task_name, payload)
        print("✅ Blog log saved to Notion:", task_name)
        return res

    except Exception as e:
        print("⚠️ Lỗi create_blog_log:", e)
        return None

def get_hexagram_log():
    res = notion.get_hexagram()
    return res

def create_hexagram_log(
    Date: str,
    Effect: str = "",
    Nhan: str = "",
    Hexagram: str = "",
    Thien: str = "",
    Scores: str = "",
    Dia: str = "",
    Summary: str = "",
    Flags: str = "",
    KeyEvent: str = "",
    Health: str = "",
    Finance: str = "",
    Psychology: str = "",
    Work: str = "",
    Trend: str = "",
    Family: str = "",
    Spiritual: str = "",
    Community: str = "",
):
    """
    📌 Tạo mới một blog trong Notion (Kanban Blog Database).
    """
    try:
        payload = {
           "Effect": {
                "rich_text": [
                    {"text": {"content":  _safe_text(Effect)}}
                ]
            },
            "Nhan": {
                "rich_text": [
                    {"text": {"content": _safe_text(Nhan)}}
                ]
            },
            "Hexagram": {
                "rich_text": [
                    {"text": {"content": _safe_text(Hexagram)}}
                ]
            },
            "Thien": {
                "rich_text": [
                    {"text": {"content": _safe_text(Thien)}}
                ]
            },
            "Scores": {
                "rich_text": [
                    {"text": {"content": _safe_text(Scores)}}
                ]
            },
            "Dia": {
                "rich_text": [
                    {"text": {"content": _safe_text(Dia)}}
                ]
            },
            "Summary": {
                "rich_text": [
                    {"text": {"content": _safe_text(Summary)}}
                ]
            },
            "Flags": {
                "rich_text": [
                    {"text": {"content": _safe_text(Flags)}}
                ]
            },
            "KeyEvent": {
                "rich_text": [
                    {"text": {"content": _safe_text(KeyEvent)}}
                ]
            },
            "Health": {
                "rich_text": [
                    {"text": {"content": _safe_text(Health)}}
                ]
            },
            "Finance": {
                "rich_text": [
                    {"text": {"content": _safe_text(Finance)}}
                ]
            },
            "Psychology": {
                "rich_text": [
                    {"text": {"content": _safe_text(Psychology)}}
                ]
            },
            "Work": {
                "rich_text": [
                    {"text": {"content": _safe_text(Work)}}
                ]
            },
            "Trend": {
                "rich_text": [
                    {"text": {"content": _safe_text(Trend)}}
                ]
            },
            "Family": {
                "rich_text": [
                    {"text": {"content": _safe_text(Family)}}
                ]
            },
            "Spiritual": {
                "rich_text": [
                    {"text": {"content": _safe_text(Spiritual)}}
                ]
            },
            "Community": {
                "rich_text": [
                    {"text": {"content": _safe_text(Community)}}
                ]
            },
        }

        res = notion.update_hexagram(Date, payload)
        print("✅ Blog log saved to Notion:", Date)
        return res

    except Exception as e:
        print("⚠️ Lỗi create_blog_log:", e)
        return None


