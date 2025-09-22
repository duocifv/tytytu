# nodes.py
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from typing_extensions import TypedDict

from brain.policy import PolicyEngine
from brain.tiny_ml import TinyML
from brain.notion_logger import done_log, failed_log, start_log, not_started_log
from brain.types import State

# Node imports
from nodes.keyword_node import keyword_node
from nodes.research_node import research_node
from nodes.insight_node import insight_node
from nodes.idea_node import idea_node
from nodes.title_node import title_node
from nodes.content_node import content_node
from nodes.image_node import image_node
from nodes.seo_node import seo_node
from nodes.publish_node import publish_node
from nodes.finalize_node import finalize_node

# =========================
# Khởi tạo Brain & Policy
# =========================
tiny_ml = TinyML()
policy = PolicyEngine()

# =========================
# Map node name -> function
# =========================
node_map = {
    "keyword": keyword_node,
    "research": research_node,
    "insight": insight_node,
    "idea": idea_node,
    "title": title_node,
    "content": content_node,
    "image": image_node,
    "seo": seo_node,
    "publish": publish_node,
}

# =========================
# Node 1: AI quyết định sequence
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

    if node_name not in state["status"].get("nodes", {}):
        not_started_log(node_name)

    if not policy.can_run(node_name):
        state["status"]["step"] = step + 1
        failed_log(node_name)
        return state

    start_log(node_name)
    policy.register_run(node_name)

    out = node_map[node_name](state)
    status = out.get("status", "failed")

    if status not in ("done", "failed", "retry"):
        warn_msg = f"Node '{node_name}' returned unknown status: {status}. Treating as failed."
        print("WARNING:", warn_msg)
        state["messages"].append(HumanMessage(content=warn_msg))
        status = "failed"

    retries = state.get("retries", {})
    retries.setdefault(node_name, 0)

    if status == "retry":
        if retries[node_name] < policy.max_retry:
            retries[node_name] += 1
            state["retries"] = retries
            return state
        else:
            status = "failed"

    if status == "failed":
        if retries[node_name] < policy.max_retry:
            retries[node_name] += 1
            state["retries"] = retries
            return state
        else:
            state["status"]["step"] = step + 1
            failed_log(node_name)
            msg = f"Node {node_name} failed and skipped after {retries[node_name]} retries"
            state["messages"].append(HumanMessage(content=msg))
            return state

    if status == "done":
        msgs = out.get("messages", [])
        if msgs:
            state["messages"].extend(msgs)

        state["status"]["nodes"] = state["status"].get("nodes", {})
        state["status"]["nodes"][node_name] = "done"
        state["status"]["step"] = step + 1

        state["outputs"][node_name] = out.get("outputs", {})

        if "seo_score" in out or "meta" in out:
            state["status"].setdefault("node_data", {})
            state["status"]["node_data"].setdefault(node_name, {})
            for k in ("seo_score", "meta"):
                if k in out:
                    state["status"]["node_data"][node_name][k] = out[k]

        done_log(node_name)
        return state

# =========================
# Build workflow graph
# =========================
def build_graph():
    workflow = StateGraph(State)

    workflow.add_node("decide_sequence", decide_sequence_node)
    workflow.add_node("runner", runner_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("decide_sequence")
    workflow.add_edge("decide_sequence", "runner")

    workflow.add_conditional_edges(
        "runner",
        lambda state: (
            "runner"
            if state["status"]["step"] < len(state["status"]["sequence"])
            else "finalize"
        )
    )

    workflow.add_edge("finalize", END)
    return workflow
