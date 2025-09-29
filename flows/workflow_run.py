import uuid
import threading
import logging
import time

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from brain.nodes import build_graph
from brain.types import State

logger = logging.getLogger("workflow")

running = False
graph = None

lock = threading.Lock()

def setup_graph():
    """Khởi tạo workflow"""
    memory = MemorySaver()
    workflow = build_graph()
    compiled = workflow.compile(checkpointer=memory)
    return compiled


def loop(thread_name: str = "telegram-thread"):
    """Chạy workflow đúng 1 vòng rồi tắt"""
    global running, graph
    if not graph:
        graph = setup_graph()

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    init_state: State = {
        "messages": [HumanMessage(content="mở quẻ")],
        "outputs": {
            "keyword": [],
            "research": [],
            "insight": [],
            "idea": [],
            "title": "",
            "content": "",
            "publish": {}
        },
        "retries": {},
        "topic": "Sức khỏe",
        "status": {
            "sequence": 0,
            "step": "init",
            "done_nodes": []
        },
        "daily": {
                "thien": "",
                "dia": "",
                "nhan": "",
                "key_event": "",
                "node_id": "",
                "timestamp": "",
                "Thien": "",
                "Dia": "",
                "Nhan": "",
                "KeyEvent": "",
                "llm_summary": "",
                "llm_key_event_effect": "",
                "scores": {"H1":0,"H2":0,"H3":0,"H4":0,"H5":0,"H6":0},
                "bits_h1_h6": [0,0,0,0,0,0],
                "moving_flags": [False,False,False,False,False,False],
                "base": {"bitstring":"", "id":0, "name":"", "bits":"", "relations":{}},
                "transformed": {"bitstring":"", "id":0, "name":"", "bits":"", "relations":{}},
                "health": "",
                "finance": "",
                "psychology": "",
                "work": "",
                "trend": "",
                "note": ""
            }
    }

    # 1. Chạy workflow
    state1 = graph.invoke(init_state, config=config)
    logger.info("Kết quả workflow:")
    for msg in state1["messages"]:
        logger.info("- %s", msg.content)

    # 2. Resume trước publish
    # history = list(graph.get_state_history(config))
    # cp = next(
    #     (
    #         h for h in reversed(history)
    #         if not any(
    #             "publish" in (m.content if hasattr(m, "content") else str(m)).lower()
    #             for m in h.values.get("messages", [])
    #         )
    #     ),
    #     None
    # )

    # if cp:
    #     resumed_state = graph.invoke(
    #         None,
    #         config={
    #             "configurable": {
    #                 "thread_id": thread_id,
    #                 "checkpoint_id": cp.config["configurable"]["checkpoint_id"]
    #             }
    #         },
    #     )
    #     logger.info("Kết quả resume trước publish:")
    #     for msg in resumed_state["messages"]:
    #         logger.info("- %s", msg.content)

    # ✅ tự tắt sau khi chạy xong
    running = False
    logger.info("Workflow đã hoàn tất và dừng.")

    # time.sleep(999999)  # delay cực dài


def start_workflow():
    global running
    with lock:
        if not running:
            running = True
            logger.info("=== BẮT ĐẦU workflow thread ===")
            threading.Thread(target=loop, daemon=True).start()
        else:
            logger.info("⚠️ Workflow đã chạy, bỏ qua request mới")
