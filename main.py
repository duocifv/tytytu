import asyncio
from services.notion_service import NotionService
from nodes.manager import run_blog_workflow

if __name__ == "__main__":
    notion_client = NotionService()
    asyncio.run(run_blog_workflow(notion_client))
