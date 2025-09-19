from chains.coordination_chain import run_coordination_chain

class CoordinationNode:
    def run(self, input_text: str):
        print("\n📌 Node_3: Trung tâm (PM + CSKH)")
        results = run_coordination_chain(input_text)
        print(f"results run_operations_chain {results}")

        # Lấy text trực tiếp
        final_result = results.content if hasattr(results, "content") else str(results)
        return {
            "name": f"Kế hoạch & báo cáo dựa trên: ",
            "final_result": final_result,
            "properties": {
                "Stage": {
                    "relation": [{"id": "27052996-7a0c-8046-a35d-c17562ae3309"}]
                },
                "Team": {
                    "relation": [{"id": "27052996-7a0c-80b6-a222-e2af5fee7d28"}]
                }
            }
        }
