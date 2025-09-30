from langchain_core.messages import HumanMessage

from brain.notion_logger import create_hexagram_log

def finalize_node(state):
    messages = []
    print(f"🔹 Finalize node state dump --------------------> :", state)

    daily = state.get("daily", {})

    # --- Lấy dữ liệu từ state['daily'] để truyền vào Notion ---
    create_hexagram_log(
        Date=daily.get("timestamp", "").split("T")[0],
        Effect=daily.get("llm_key_event_effect", ""),
        Nhan=daily.get("nhan", ""),
        Hexagram=daily.get("base", {}).get("name", ""),
        Thien=daily.get("thien", ""),
        Scores=str(daily.get("scores", {})),
        Dia=daily.get("dia", ""),
        Summary=daily.get("llm_summary", ""),
        Flags=", ".join([str(f) for f in daily.get("moving_flags", [])]),
        KeyEvent=daily.get("KeyEvent", "") or daily.get("key_event", ""),
        Health=daily.get("health", ""),
        Finance=daily.get("finance", ""),
        Psychology=daily.get("psychology", ""),
        Work=daily.get("work", ""),
        Trend=daily.get("trend", ""),
        Note=daily.get("note", "")
    )

    print("✅ Đã gửi dữ liệu lên Notion")
    messages.append(HumanMessage(content="✅ Blog saved to Notion"))

    return {
        "status": "done",
        "messages": messages,
    }
