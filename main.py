from nodes.manager import ManagerNode

if __name__ == "__main__":
    customer_request = "Viết bài blog về AI cho khách hàng X"

    manager = ManagerNode()
    final_result = manager.run(customer_request)

    print("\n🎯 Kết quả cuối cùng:", final_result)
