from chains.operations_chain import run_operations_chain

class OperationsNode:
    def run(self, request: str):
        print("\n📌 Node_1: Phân tích Yêu cầu")

        # results là AIMessage
        results = run_operations_chain(request)
        print(f"results run_operations_chain {results}")
        # Lấy text trực tiếp
        final_result = results.content if hasattr(results, "content") else str(results)

        return {
            "name": f"Hoàn tất phân tích & chuyển giao cho: {request}",
            "final_result": final_result,
            "properties": {
                "Stage": {
                    "relation": [{"id": "27052996-7a0c-809f-8420-cda068eb861e"}]
                },
                "Team": {
                    "relation": [{"id": "27052996-7a0c-80b6-a222-e2af5fee7d28"}]
                },
            }
        }
