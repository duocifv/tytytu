from services.hexagram_service import HexagramService
import json

# Quick run example
if __name__ == "__main__":
    svc = HexagramService()
    # if you want VN names (Sino-Vietnamese) or your own King-Wen list, call:
    # svc.set_names(your_64_list)

    info = svc.relations_of("乾 Qián - The Creative")
    print("=== JSON (detailed relations_of) ===")
    print(json.dumps(info, ensure_ascii=False, indent=2))

    print("\n=== Compact (ids only) ===")
    print(json.dumps(svc.relations_compact("乾 Qián - The Creative"), ensure_ascii=False, indent=2))

    print("\n=== Mô tả gọn ===")
    print(svc.describe_hexagram("乾 Qián - The Creative"))
