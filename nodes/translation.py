from chains.translation_chain import run_translation_chain

class TranslationNode:
    def run(self, input_text: str):
        print("\n📌 Node_2: Thông dịch")
        results = run_translation_chain(input_text)
        print(f"results run_operations_chain {results}")
        
        # Lấy text trực tiếp
        final_result = results.content if hasattr(results, "content") else str(results)
        return {
            "name": f"Brief chuẩn từ:",
            "final_result": final_result,
            "properties": {
                "Stage": {
                    "relation": [{"id": "27052996-7a0c-8052-8e14-e219285ac094"}]
                },
                "Team": {
                    "relation": [{"id": "27052996-7a0c-80b6-a222-e2af5fee7d28"}]
                }
            }
        } 
