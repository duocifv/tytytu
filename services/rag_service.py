# services/rag_service.py
class RAGRetriever:
    def __init__(self, sources=None):
        self.sources = sources or []

    def retrieve(self, notion_data):
        # Trả về dữ liệu giả lập từ "nguồn thực tế"
        return "Thông tin thực tế giả lập từ các nguồn: " + ", ".join(self.sources)
