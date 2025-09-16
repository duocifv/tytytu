from chains.base import SequentialChain

def build_publish_chain():
    def aggregate_result(x): return f"📦 Tổng hợp kết quả từ: {x}"
    def publish_blog(x): return f"🌐 Xuất bản blog với nội dung: {x}"

    return SequentialChain([
        aggregate_result, publish_blog
    ])
