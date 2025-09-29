import os
from dotenv import load_dotenv
import httpx
from datetime import datetime
from typing import Dict

# Load biến môi trường từ .env
load_dotenv()

NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "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")
NOTION_DATA_SOURCE_ID = os.getenv("NOTION_DATA_SOURCE_ID", "2829eecf-c4f8-4a1f-94b6-71553b7404d7")
SOURCE_ID_PROJECT = os.getenv("SOURCE_ID_PROJECT", "27052996-7a0c-805a-8500-000b0c8d4764")
SOURCE_ID_BLOG = os.getenv("SOURCE_ID_BLOG", "27152996-7a0c-8056-9210-000b61c8a5d6")
SOURCE_ID_HEXAGRAM = os.getenv("SOURCE_ID_HEXAGRAM", "27d52996-7a0c-802f-a3b9-000b5a3755bc")


HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
}


class NotionService:
    def __init__(self):
        self.task_ids = {}
        self.task_blogs: Dict[str, Dict] = {} 
        self.task_hexagram: Dict[str, Dict] = {} 
        self.client = httpx.Client(timeout=120)

    def create_task(self, task_name: str, start=None, deadline=None):
    
        start = start or datetime.today().isoformat()
        deadline = deadline or datetime.today().isoformat()

        data = {
            "parent": {"type": "data_source_id", "data_source_id": SOURCE_ID_PROJECT},
            "properties": {
                "Name": {"title": [{"text": {"content": task_name}}]},
                "Start": {"date": {"start": start}},
                "Deadline": {"date": {"start": deadline}},
            }
        }

        res = self.client.post(
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

    def update_task(self, task_name: str, properties: dict):

        if task_name not in self.task_ids:
             self.create_task(task_name)

        page_id = self.task_ids.get(task_name)
        if not page_id:
            print(f"⚠️ Không tìm thấy blog '{task_name}' để cập nhật")
            return
        
        res = self.client.patch(
            f"{NOTION_API_URL}/{page_id}",
            headers={**HEADERS, "Notion-Version": "2025-09-03"}, 
            json={"properties": properties}
        )
        if res.status_code in [200, 201]:
            print(f"✅ Update task '{task_name}'")
        else:
            print("⚠️ Lỗi update task:", res.text)

    def finalize_task(self, name: str):
        self.update_task(name, {"KPI": {"number": 100}})
        print(f"🏁 Hoàn tất task '{name}'")

    def get_relation_mapping(self, database_id):
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        res = self.client.post(
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

    def create_blog(self, task_name: str):
        data = {
            "parent": {"type": "data_source_id", "data_source_id": SOURCE_ID_BLOG},
            "properties": {
                "Name": {"title": [{"text": {"content": task_name}}]},
            }
        }
        res = self.client.post(
            NOTION_API_URL, 
            headers={**HEADERS, "Notion-Version": "2025-09-03"}, 
            json=data)
            
        if res.status_code in [200, 201]:
            page_id = res.json()["id"]
            self.task_blogs[task_name] = page_id
            print(f"📌 Tạo blog '{task_name}' trên Notion")
        else:
            print("⚠️ Lỗi tạo blog:", res.text)

    def update_blog(self, task_name: str, properties: dict):
        if task_name not in self.task_blogs:
             self.create_blog(task_name)
             
        # if not blogId:
        #     print(f"⚠️ Không tìm thấy blog '{task_name}' để cập nhật")
        #     return
        
        blogId = self.task_blogs.get(task_name)
        res = self.client.patch(
            f"{NOTION_API_URL}/{blogId}",
            headers={**HEADERS, "Notion-Version": "2025-09-03"}, 
            json={"properties": properties}
        )

        if res.status_code in [200, 201]:
            print(f"✅ Update task '{task_name}'")
        else:
            print("⚠️ Lỗi update task:", res.text)


    def create_hexagram(self, task_name: str):
        data = {
            "parent": {"type": "data_source_id", "data_source_id": SOURCE_ID_HEXAGRAM},
            "properties": {
               "Date": {"title": [{"text": {"content": task_name}}]},
            }
        }
        res = self.client.post(
            NOTION_API_URL, 
            headers={**HEADERS, "Notion-Version": "2025-09-03"}, 
            json=data)
            
        if res.status_code in [200, 201]:
            page_id = res.json()["id"]
            self.task_hexagram[task_name] = page_id
            print(f"📌 Tạo blog '{task_name}' trên Notion")
        else:
            print("⚠️ Lỗi tạo blog:", res.text)

    def update_hexagram(self, task_name: str, properties: dict):
        if task_name not in self.task_hexagram:
             self.create_hexagram(task_name)
             
        # if not blogId:
        #     print(f"⚠️ Không tìm thấy blog '{task_name}' để cập nhật")
        #     return
        
        hexagramId = self.task_hexagram.get(task_name)
        res = self.client.patch(
            f"{NOTION_API_URL}/{hexagramId}",
            headers={**HEADERS, "Notion-Version": "2025-09-03"}, 
            json={"properties": properties}
        )

        if res.status_code in [200, 201]:
            print(f"✅ Update task '{task_name}'")
        else:
            print("⚠️ Lỗi update task:", res.text)
    
    def get_blog(self, name: str):
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
        res = self.client.post(url, headers=HEADERS, json=payload)
        if res.status_code != 200:
            print("⚠️ Lỗi lấy blog:", res.text)
            return None

        results = res.json().get("results", [])
        if results:
            return results[0]  # trả về page đầu tiên
        return None

    async def aclose(self):
        await self.client.aclose()
