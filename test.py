import uuid
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from brain.nodes import State, build_graph

if __name__ == "__main__":
    init_state: State = {
        "status": {},
        "results": {"messages": [HumanMessage(content="Bắt đầu workflow")]},
        "retries": {},
        "topic": "Thiền và tâm lý học hiện đại"
    }

    memory = MemorySaver()
    workflow = build_graph()
    graph = workflow.compile(checkpointer=memory)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # 1. Chạy workflow
    state1 = graph.invoke(init_state, config=config)
    print("Kết quả workflow:")
    for msg in state1["results"]["messages"]:
        print("-", msg.content)

    # 2. Resume trước publish
    history = list(graph.get_state_history(config))
    cp = next(
        (h for h in reversed(history)
         if not any("publish" in (m.content if hasattr(m, "content") else str(m)).lower()
                    for m in h.values.get("results", {}).get("messages", []))),
        None
    )

    if cp:
        resumed_state = graph.invoke(
            None,
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": cp.config["configurable"]["checkpoint_id"]
                }
            },
        )
        print("\nKết quả resume trước publish:")
        for msg in resumed_state["results"]["messages"]:
            print("-", msg.content)
