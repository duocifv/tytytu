class PolicyEngine:
    def __init__(self):
        self.daily_max_nodes = 3
        self.retry_limit = 2
        self.node_run_count = {}
        self.node_retry_count = {}

    def can_run(self, node_name):
        if self.node_run_count.get(node_name, 0) >= self.daily_max_nodes:
            return False
        return True

    def register_run(self, node_name):
        self.node_run_count[node_name] = self.node_run_count.get(node_name, 0) + 1

    def can_retry(self, node_name):
        return self.node_retry_count.get(node_name, 0) < self.retry_limit

    def register_retry(self, node_name):
        self.node_retry_count[node_name] = self.node_retry_count.get(node_name, 0) + 1
