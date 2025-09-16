import requests
import os
from datetime import datetime

NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "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")
NOTION_DATA_SOURCE_ID = os.getenv("NOTION_DATA_SOURCE_ID", "2829eecf-c4f8-4a1f-94b6-71553b7404d7")

SOURCE_ID_PROJECT = os.getenv("NOTION_DATA_SOURCE_ID", "27052996-7a0c-805a-8500-000b0c8d4764")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
}

class NotionService:
    def __init__(self):
        self.task_ids = {}

    def create_task(self, name: str, start=None, deadline=None):
        """Tạo task mới với schema Project database"""
        start = start or datetime.today().isoformat()
        deadline = deadline or datetime.today().isoformat()

        data = {
            "parent": { 
                "type": "data_source_id", 
                "data_source_id": SOURCE_ID_PROJECT
            },
            "properties": {
                "Name": { 
                    "title": [
                        { "text": { "content": name } }
                    ]
                },
                "Start": { 
                    "date": { "start": start } 
                },
                "Deadline": { 
                    "date": { "start": deadline } 
                },
               "Status": {
                   "status": { "name": "Đang làm" }
                },
            }
        }

        res = requests.post(
            NOTION_API_URL,
            headers={**HEADERS, "Notion-Version": "2025-09-03"},
            json=data
        )

        if res.status_code in [200, 201]:
            page_id = res.json()["id"]
            self.task_ids[name] = page_id
            print(f"📌 Tạo task '{name}' cho project '{name}' trên Notion")
        else:
            print("⚠️ Lỗi tạo task:", res.text)

    def update_task(self, name: str, properties: dict):
        """updates là dict mapping tên cột → giá trị mới"""
        page_id = self.task_ids.get(name)
        if not page_id:
            return

        res = requests.patch(
            f"{NOTION_API_URL}/{page_id}",
            headers={**HEADERS, "Notion-Version": "2025-09-03"},
            json={"properties": properties}
        )
        if res.status_code in [200, 201]:
            print(f"✅ Update task '{name}' trên Notion")
        else:
            print("⚠️ Lỗi update task:", res.text)

    def finalize_task(self, name: str):
        """Ví dụ đánh dấu KP = 100 khi hoàn tất"""
        self.update_task(name, {"KP": 100})
        print(f"🏁 Hoàn tất task '{name}' trên Notion")

    def get_relation_mapping(self, database_id):
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        res = requests.post(url, headers=HEADERS)
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
