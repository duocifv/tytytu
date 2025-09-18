import os
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

def log_node(node_name: str, status: str, message: str):
    """
    Tạo một page trong database Notion cho node workflow.
    """
    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "Node": {"title": [{"text": {"content": node_name}}]},
            "Status": {"select": {"name": status}},
            "Message": {"rich_text": [{"text": {"content": message}}]},
            "Timestamp": {"date": {"start": datetime.now().isoformat()}}
        }
    )


########################:::::docs:::::::https://pypi.org/project/notion-client/