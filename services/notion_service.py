import os
import httpx
from datetime import datetime
from typing import Dict

NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "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")
NOTION_DATA_SOURCE_ID = os.getenv("NOTION_DATA_SOURCE_ID", "2829eecf-c4f8-4a1f-94b6-71553b7404d7")
SOURCE_ID_PROJECT = os.getenv("SOURCE_ID_PROJECT", "27052996-7a0c-805a-8500-000b0c8d4764")
SOURCE_ID_BLOG = os.getenv("SOURCE_ID_BLOG", "27152996-7a0c-8056-9210-000b61c8a5d6")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
}



class NotionService:
    def __init__(self):
        self.task_ids = {}
        self.task_blog: Dict[str, Dict] = {}  # lưu dữ liệu các task
        self.client = httpx.AsyncClient(timeout=20)

    async def create_task(self, task_name: str, start=None, deadline=None):
    
        start = start or datetime.today().isoformat()
        deadline = deadline or datetime.today().isoformat()

        data = {
            "parent": {"type": "data_source_id", "data_source_id": SOURCE_ID_PROJECT},
            "properties": {
                "Name": {"title": [{"text": {"content": task_name}}]},
                "Start": {"date": {"start": start}},
                "Deadline": {"date": {"start": deadline}},
                "Status": {"status": {"name": "Bắt đầu"}},
            }
        }

        res = await self.client.post(
            NOTION_API_URL,
            headers={**HEADERS, "Notion-Version": "2025-09-03"},
            json=data
        )

        if res.status_code in [200, 201]:
            page_id = res.json()["id"]
            self.task_ids[task_name] = page_id
            print(f"📌 Tạo task '{task_name}' trên Notion")
        else:
            print("⚠️ Lỗi tạo task:", res.text)
            return None

    async def update_task(self, task_name: str, properties: dict):
        page_id = self.task_ids.get(task_name)

        if task_name not in self.task_ids:
            await self.create_task(task_name)

        if not page_id:
            print(f"⚠️ Không tìm thấy blog '{task_name}' để cập nhật")
            return
        
        res = await self.client.patch(
            f"{NOTION_API_URL}/{page_id}",
            headers={**HEADERS, "Notion-Version": "2025-09-03"}, 
            json={"properties": properties}
        )
        if res.status_code in [200, 201]:
            print(f"✅ Update task '{task_name}'")
        else:
            print("⚠️ Lỗi update task:", res.text)

    async def finalize_task(self, name: str):
        await self.update_task(name, {"KPI": {"number": 100}})
        print(f"🏁 Hoàn tất task '{name}'")

    async def get_relation_mapping(self, database_id):
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        res = await self.client.post(
                url,
                headers={**HEADERS, "Notion-Version": "2022-06-28"},
            )
        if res.status_code != 200:
            print("⚠️ Lỗi query database:", res.text)
            return {}
        mapping = {}
        for page in res.json().get("results", []):
            page_id = page["id"]
            title_list = page["properties"].get("Name", {}).get("title", [])
            if title_list:
                name = title_list[0]["text"]["content"]
                mapping[name] = page_id
        return mapping

    async def create_blog(self, task_name: str, topic="", audience="", guideline="", keywords="", outline="", facts="", content="", images="", video="", status="Đang làm"):
        data = {
            "parent": {"type": "data_source_id", "data_source_id": SOURCE_ID_BLOG},
            "properties": {
                "Name": {"title": [{"text": {"content": task_name}}]},
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
            }
        }
        res = await self.client.post(
            NOTION_API_URL, 
            headers={**HEADERS, "Notion-Version": "2025-09-03"}, 
            json=data)
            
        if res.status_code in [200, 201]:
            page_id = res.json()["id"]
            self.task_blog["id"] = page_id
            print(f"📌 Tạo blog '{task_name}' trên Notion")
        else:
            print("⚠️ Lỗi tạo blog:", res.text)

    async def update_blog(self, task_name: str, properties: dict):
        blogId = self.task_blog.get(task_name)

        if not blogId:
            print(f"⚠️ Không tìm thấy blog '{task_name}' để cập nhật")
            return
        
        res = await self.client.patch(
            f"{NOTION_API_URL}/{blogId}",
            headers={**HEADERS, "Notion-Version": "2025-09-03"}, 
            json={"properties": properties}
        )

        if res.status_code in [200, 201]:
            print(f"✅ Update task '{task_name}'")
        else:
            print("⚠️ Lỗi update task:", res.text)
    
    async def get_blog(self, name: str):
        """
        Lấy thông tin blog theo Name từ database.
        """
        url = f"https://api.notion.com/v1/databases/{SOURCE_ID_PROJECT}/query"
        payload = {
            "filter": {
                "property": "Name",
                "title": {"equals": name}
            }
        }
        res = await self.client.post(url, headers=HEADERS, json=payload)
        if res.status_code != 200:
            print("⚠️ Lỗi lấy blog:", res.text)
            return None

        results = res.json().get("results", [])
        if results:
            return results[0]  # trả về page đầu tiên
        return None

    async def aclose(self):
        await self.client.aclose()
