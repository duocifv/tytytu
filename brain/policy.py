# brain/policy.py
from datetime import date

class PolicyEngine:
    def __init__(self):
        # Giới hạn đơn giản theo node (có thể nâng cấp lưu DB)
        self.daily_counts = {}           # { node_name: count_today }
        self.max_per_day = 3             # mỗi node tối đa chạy 3 lần/ngày
        self.max_retry = 2               # tối đa retry cho mỗi node

        # optional: track date so counts reset mỗi ngày
        self._last_day = date.today()

    def _maybe_reset(self):
        today = date.today()
        if today != self._last_day:
            self.daily_counts = {}
            self._last_day = today

    def can_run(self, node_name: str) -> bool:
        self._maybe_reset()
        return self.daily_counts.get(node_name, 0) < self.max_per_day

    def register_run(self, node_name: str):
        self._maybe_reset()
        self.daily_counts[node_name] = self.daily_counts.get(node_name, 0) + 1

    def can_retry(self, node_name: str) -> bool:
        # You can add extra logic here, for now always allow
        return True
