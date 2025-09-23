import uuid
import time
import threading
from fastapi import FastAPI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from brain.nodes import build_graph
import uvicorn
from contextlib import asynccontextmanager
from brain.types import State
from flows.workflow_run import start_workflow

# # Biến điều khiển
# running = False
# graph = None


# def setup():
#     """Khởi tạo workflow"""
#     memory = MemorySaver()
#     workflow = build_graph()
#     return workflow.compile(checkpointer=memory)


# def loop():
#     """Loop workflow khi bật"""
#     global running, graph
#     while running:
#         thread_id = str(uuid.uuid4())
#         config = {"configurable": {"thread_id": thread_id}}

#         init_state: State = {
#             "messages": [HumanMessage(content="Bắt đầu workflow")],
#             "outputs": {
#                 "keyword": [],
#                 "research": [],
#                 "insight": [],
#                 "idea": [],
#                 "title": "",
#                 "content": "",
#                 "publish": {}
#             },
#             "retries": {},
#             "topic": "Sức khỏe",
#             "status": {
#                 "sequence": 0,
#                 "step": "init",
#                 "done_nodes": []
#             }
#         }

#         # 1. Chạy workflow
#         state1 = graph.invoke(init_state, config=config)
#         print("Kết quả workflow:")
#         for msg in state1["messages"]:
#             print("-", msg.content)

#         # 2. Resume trước publish
#         history = list(graph.get_state_history(config))
#         cp = next(
#             (
#                 h for h in reversed(history)
#                 if not any(
#                     "publish" in (m.content if hasattr(m, "content") else str(m)).lower()
#                     for m in h.values.get("messages", [])
#                 )
#             ),
#             None
#         )

#         if cp:
#             resumed_state = graph.invoke(
#                 None,
#                 config={
#                     "configurable": {
#                         "thread_id": thread_id,
#                         "checkpoint_id": cp.config["configurable"]["checkpoint_id"]
#                     }
#                 },
#             )
#             print("\nKết quả resume trước publish:")
#             for msg in resumed_state["messages"]:
#                 print("-", msg.content)

#         time.sleep(5)  # giống Arduino delay


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global graph
#     # chạy khi app khởi động
#     graph = setup()
#     yield
#     # cleanup khi app tắt (nếu cần)


app = FastAPI()


@app.post("/start")
def start_loop():
    print("📩 /start API called")
    start_workflow()
    return {"status": "already running"}


@app.post("/stop")
def stop_loop():
    global running
    running = False
    return {"status": "stopped"}


@app.get("/status")
def get_status():
    return {"running": running}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
