from nodes.operations import OperationsNode
from nodes.translation import TranslationNode
from nodes.coordination import CoordinationNode
from nodes.brand import BrandNode
from services.notion_service import NotionService
from datetime import datetime

class ManagerNode:
    def __init__(self):
        self.nodes = {
            "Phân tích yêu cầu": OperationsNode(),
            "Thông dịch & chuẩn hóa": TranslationNode(),
            "Trung tâm PM+CSKH": CoordinationNode(),
            "Quản trị thương hiệu": BrandNode(),
        }
        self.progress = []
        self.notion = NotionService()
        self.project_name = "Dự án số 2"

    def log_progress(self, team: str, result):
        msg = result.get("name") if isinstance(result, dict) else str(result)
        print(f"📊 [Báo cáo] {team}: {msg}")
        self.progress.append(f"{team}: {msg}")

        # Cập nhật task Notion
        task_name = f"{self.project_name} - {team}"
        if task_name not in self.notion.task_ids:
            self.notion.create_task(task_name, start=datetime.today().isoformat())
        self.notion.update_task(task_name, {
            "Status": {"status": {"name": "Đang làm"}},
        })

    def finalize_task(self, team: str):
        task_name = f"{self.project_name} - {team}"
        self.notion.update_task(task_name, {
            "Status": {"status": {"name": "Hoàn tất"}}
        })
        self.notion.finalize_task(task_name)

    def run(self, request: str):
        print("==> Manager: 🚀 Điều phối & giám sát tiến độ toàn bộ workflow")
        data = request

        for team, node in self.nodes.items():
            self.log_progress(team,"New Project")
            data = node.run(data)  # Gọi node, trả về kết quả
            self.log_progress(team, data)
            self.finalize_task(team)

        print("\n📑 Báo cáo tổng kết tiến độ:")
        for line in self.progress:
            print("   -", line)

        return data  # Kết quả cuối cùng từ Node 4
