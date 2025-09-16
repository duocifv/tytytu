from chains.base import SequentialChain

def build_manager_chain():
    def create_task(x): return f"📝 Tạo task từ: {x}"
    def assign_task(x): return f"👥 Phân công công việc dựa trên: {x}"
    def monitor_task(x): return f"📊 Giám sát & báo cáo tiến độ của: {x}"

    return SequentialChain([
        create_task, assign_task, monitor_task
    ])
