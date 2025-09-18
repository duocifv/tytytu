import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command

import chromadb
import uuid

load_dotenv()

# -------------------------
# State
class State(TypedDict):
    messages: Annotated[list, add_messages]
    vector_results: list

# -------------------------
# Tools
@tool
def fake_search(query: str) -> str:
    """Tìm kiếm văn bản."""
    return f"[FAKE SEARCH] Kết quả tìm kiếm cho: {query}"

@tool
def human_assistance(query: str) -> str:
    """yêu cầu từ người."""
    response = interrupt({"query": query})
    return response["data"]

@tool
def summarize(text: str) -> str:
    """Tóm tắt văn bản."""
    return f"[SUMMARY] {text[:50]}..."

tools = [fake_search, human_assistance, summarize]

# -------------------------
# ChromaDB client (Persistent)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection_name = "demo_collection"

def save_doc(content: str, metadata=None):
    collection = chroma_client.get_or_create_collection(name="demo_collection")
    doc_id = f"doc_{str(uuid.uuid4())[:8]}"

    if not metadata:
        metadata = {"source": "demo"}

    collection.upsert(
        documents=[content],
        metadatas=[metadata],
        ids=[doc_id]
    )
    return doc_id

def search_docs(query: str, top_k=2):
    collection = chroma_client.get_or_create_collection(name=collection_name)
    results = collection.query(query_texts=[query], n_results=top_k)
    return results.get("documents", [[]])[0]

# Khởi tạo dữ liệu mẫu
for item in ["bánh mì", "cà phê", "trà", "sữa", "mì tôm"]:
    save_doc(f"Mô tả về {item}")

# -------------------------
# Nodes
def node1_search(state: State):
    msg = fake_search.invoke(state["messages"][-1].content)
    state["messages"].append(HumanMessage(content=msg))
    return {"messages": [HumanMessage(content=msg)]}

def node2_vector(state: State):
    query = state["messages"][-1].content
    results = search_docs(query, top_k=2)
    state["vector_results"] = results
    return {"messages": [HumanMessage(content=" | ".join(results))]}

def node3_summarize(state: State):
    last = state["messages"][-1].content
    msg = summarize.invoke(last)
    return {"messages": [HumanMessage(content=msg)]}

def node4_human(state: State):
    msg = human_assistance.invoke(state["messages"][-1].content)
    return {"messages": [HumanMessage(content=msg)]}

# Dummy nodes 5-10
def make_dummy_node(name):
    def node(state: State):
        txt = state["messages"][-1].content
        return {"messages": [HumanMessage(content=f"[{name}] {txt}")] }
    return node

dummy_nodes = {f"node{i}": make_dummy_node(f"node{i}") for i in range(5, 11)}

# -------------------------
# Manager Node
def manager_node(state: State):
    last_msg = state["messages"][-1].content.lower()
    results = []

    if "bánh mì" in last_msg:
        r1 = node1_search(state)
        r2 = node2_vector(state)
        r3 = node3_summarize(state)
        results.extend([
            r1["messages"][0].content,
            r2["messages"][0].content,
            r3["messages"][0].content
        ])
    elif "cà phê" in last_msg:
        r1 = node2_vector(state)
        r2 = node4_human(state)
        results.extend([
            r1["messages"][0].content,
            r2["messages"][0].content
        ])
    else:
        results.append(f"[LLM] {last_msg}")

    if state.get("vector_results"):
        results.append(f"[Vector DB] {' | '.join(state['vector_results'])}")

    final_reply = " | ".join(results)
    return {"messages": [HumanMessage(content=final_reply)]}

# -------------------------
# Graph
graph_builder = StateGraph(State)
graph_builder.add_node("manager", manager_node)

for name, node in dummy_nodes.items():
    graph_builder.add_node(name, node)

graph_builder.set_entry_point("manager")
graph_builder.add_edge("manager", END)

memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# -------------------------
# Demo
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "octopus-chroma-demo"}}

    msgs = [
        "Tôi muốn biết về bánh mì",
        "Tôi muốn cà phê ngon",
        "Nói về mì tôm"
    ]

    for i, text in enumerate(msgs, 1):
        print(f"\n=== Query {i} ===")
        out = graph.invoke({"messages": [HumanMessage(content=text)]}, config=config)
        print("Bot reply:", out["messages"][-1].content)
