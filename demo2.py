from nodes.keyword_node import keyword_node   # ✅ import node bạn vừa viết

if __name__ == "__main__":
    # Input state giả lập
    state = {
        "topic": "Sức khỏe"
    }

    # Gọi node
    result = keyword_node(state)

    # In ra kết quả
    print("\n📌 Final Output:")
    print("Status:", result["status"])
    print("Messages:", [m.content for m in result["messages"]])
    print("Outputs:", result["outputs"])
