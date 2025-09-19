from chains.brand_chain import run_brand_chain

class BrandNode:
    def run(self, input_text: str):
        print("\n📌 Node_4: Quản trị Thương hiệu")
        results =  run_brand_chain(input_text)
        print(f"results run_operations_chain {results}")

        # Lấy text trực tiếp
        final_result = results.content if hasattr(results, "content") else str(results)
        return {
            "name": f"Ý tưởng đã duyệt từ: ",
            "final_result": final_result,
            "properties": {
                "Stage": {
                    "relation": [{"id": "27052996-7a0c-80e6-bb4a-e28db24dcf08"}]
                },
                "Team": {
                    "relation": [{"id": "27052996-7a0c-80b6-a222-e2af5fee7d28"}]
                }
            }
        }
