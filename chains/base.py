class SequentialChain:
    def __init__(self, steps):
        self.steps = steps

    def run(self, input_data):
        logs = []
        result = input_data
        for step in self.steps:
            result = step(result)
            logs.append(result)  # lưu log từng bước
        return logs[-1], logs   # trả kết quả cuối + toàn bộ log
