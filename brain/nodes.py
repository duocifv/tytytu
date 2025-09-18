from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from brain.policy import PolicyEngine
from nodes2.title_node import title_node
from nodes2.content_node import content_node
from nodes2.image_node import image_node
from nodes2.seo_node import seo_node
from nodes2.publish_node import publish_node
from brain.tiny_ml import TinyML
from brain.notion_service import log_node

tiny_ml = TinyML()
policy = PolicyEngine()

class State(TypedDict):
    status: dict
    results: dict
    retries: dict  # số lần retry từng node

node_map = {
    "title": title_node,
    "content": content_node,
    "image": image_node,
    "seo": seo_node,
    "publish": publish_node
}

# =========================
# Node 1: AI Brain quyết định sequence
# =========================
def decide_sequence_node(state: State) -> State:
    sequence = tiny_ml.decide_sequence(str(state))
    state["status"]["sequence"] = sequence
    state["status"]["step"] = 0
    return state

# =========================
# Node 2: Runner thực thi từng bước
# =========================
def runner_node(state: State) -> State:
    seq = state["status"].get("sequence", [])
    step = state["status"].get("step", 0)

    if step >= len(seq):
        return state

    node_name = seq[step]

    # Kiểm tra policy: max daily run
    if not policy.can_run(node_name):
        state["status"]["step"] = step + 1
        # Log Notion
        log_node(node_name, "Failed", f"Node {node_name} failed, skipped")
        return state

    policy.register_run(node_name)
    
    # Thực thi node
    out = node_map[node_name](state)
    status = out.get("status", "done")

    # Retry nếu fail
    retries = state.get("retries", {})
    retries.setdefault(node_name, 0)

    if status != "done":
        if retries[node_name] < policy.max_retry:
            retries[node_name] += 1
            state["retries"] = retries
            return state  # retry lần sau
        else:
            # Skip node
            state["results"]["messages"].append(
                HumanMessage(content=f"Node {node_name} failed, skipped")
            )
            state["status"]["step"] = step + 1
            return state
        
    # Append messages & đánh dấu node done
    state["results"]["messages"].extend(out["messages"])
    state["status"]["nodes"] = state["status"].get("nodes", {})
    state["status"]["nodes"][node_name] = "done"
    state["status"]["step"] = step + 1

    # Log Notion
    msg_content = "\n".join([m.content for m in out["messages"]])
    log_node(node_name, "Done", msg_content)
    
    return state

# =========================
# Build graph
# =========================
def build_graph():
    workflow = StateGraph(State)
    workflow.add_node("decide_sequence", decide_sequence_node)
    workflow.add_node("runner", runner_node)
    workflow.set_entry_point("decide_sequence")
    workflow.add_edge("decide_sequence", "runner")
    workflow.add_conditional_edges(
        "runner",
        lambda state: "runner" if state["status"]["step"] < len(state["status"]["sequence"]) else END
    )
    return workflow
