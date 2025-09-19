# nodes.py
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from brain.policy import PolicyEngine
from nodes.finalize_node import finalize_node
from nodes.keyword_node import keyword_node
from nodes.title_node import title_node
from nodes.content_node import content_node
from nodes.image_node import image_node
from nodes.seo_node import seo_node
from nodes.publish_node import publish_node
from brain.tiny_ml import TinyML
from brain.notion_logger import done_log, failed_log, start_log, not_started_log


# =========================
# Khởi tạo Brain & Policy
# =========================
tiny_ml = TinyML()          # AI nhỏ quyết định sequence các bước
policy = PolicyEngine()     # Engine kiểm soát số lần retry, giới hạn


# =========================
# State Graph lưu trữ thông tin
# =========================
class State(TypedDict):
    status: dict    # thông tin tiến độ: sequence, step, nodes đã xong
    results: dict   # kết quả: messages, outputs
    retries: dict   # số lần retry cho từng node


# =========================
# Map node name -> function
# =========================
node_map = {
    "keyword": keyword_node,
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
    """
    ✅ TinyML sẽ đọc state (ngữ cảnh hiện tại) 
       và quyết định sequence (chuỗi node cần chạy).
    """
    sequence = tiny_ml.decide_sequence(str(state))   # ví dụ ["title", "content", "seo", "publish"]
    state["status"]["sequence"] = sequence
    state["status"]["step"] = 0                      # reset step về 0
    return state


# =========================
# Node 2: Runner thực thi từng bước
# =========================
def runner_node(state: State) -> State:
    seq = state["status"].get("sequence", [])
    step = state["status"].get("step", 0)

    # Nếu đã hết sequence → return state luôn
    if step >= len(seq):
        return state

    node_name = seq[step]   # Lấy node cần chạy

    # --- Nếu node chưa có trạng thái → ghi "Chưa làm" ---
    if node_name not in state["status"].get("nodes", {}):
        not_started_log(node_name)

    # --- Check Policy ---
    if not policy.can_run(node_name):
        state["status"]["step"] = step + 1
        failed_log(node_name)
        return state

    # --- Node bắt đầu → "Bắt đầu" ---
    start_log(node_name)
    policy.register_run(node_name)  # Ghi nhận lần chạy

    # --- Gọi node thực thi ---
    out = node_map[node_name](state)

    # --- Check output contract ---
    status = out.get("status", "failed")
    if status not in ("done", "failed", "retry"):
        warn_msg = f"Node '{node_name}' returned unknown status: {status}. Treating as failed."
        print("WARNING:", warn_msg)
        state["results"]["messages"].append(HumanMessage(content=warn_msg))
        status = "failed"

    # --- Đảm bảo dict retries tồn tại ---
    retries = state.get("retries", {})
    retries.setdefault(node_name, 0)

    # --- Xử lý retry ---
    if status == "retry":
        if retries[node_name] < policy.max_retry:
            retries[node_name] += 1
            state["retries"] = retries
            print(f"Node {node_name} requested retry ({retries[node_name]}/{policy.max_retry})")
            return state
        else:
            status = "failed"

    # --- Xử lý thất bại ---
    if status == "failed":
        if retries[node_name] < policy.max_retry:
            retries[node_name] += 1
            state["retries"] = retries
            print(f"Node {node_name} failed; will retry later ({retries[node_name]}/{policy.max_retry})")
            return state
        else:
            state["status"]["step"] = step + 1
            failed_log(node_name)
            msg = f"Node {node_name} failed and skipped after {retries[node_name]} retries"
            state["results"]["messages"].append(HumanMessage(content=msg))
            return state

    # --- Xử lý thành công ---
    if status == "done":
        # Lưu lại messages
        msgs = out.get("messages", [])
        if msgs:
            state["results"]["messages"].extend(msgs)

        # Ghi trạng thái node đã xong
        state["status"]["nodes"] = state["status"].get("nodes", {})
        state["status"]["nodes"][node_name] = "done"
        state["status"]["step"] = step + 1

        # Lưu toàn bộ output của node (trừ status, messages)
        state["results"].setdefault("outputs", {})
        state["results"]["outputs"][node_name] = {
            k: v for k, v in out.items() if k not in ("status", "messages")
        }

        # Riêng SEO thì lưu thêm vào node_data
        if "seo_score" in out or "meta" in out:
            state["status"].setdefault("node_data", {})
            state["status"]["node_data"].setdefault(node_name, {})
            for k in ("seo_score", "meta"):
                if k in out:
                    state["status"]["node_data"][node_name][k] = out[k]

        # Log Notion → "Hoàn thành"
        done_log(node_name)
        return state


# =========================
# Build workflow graph
# =========================
def build_graph():
    """
    ✅ Build workflow:
    - Entry point: decide_sequence
    - Runner chạy lần lượt các node trong sequence
    - Sau khi hết sequence → notion_log → telegram_notify → END
    """
    workflow = StateGraph(State)

    # Thêm các node
    workflow.add_node("decide_sequence", decide_sequence_node)
    workflow.add_node("runner", runner_node)
    workflow.add_node("finalize", finalize_node) 

    # Entry
    workflow.set_entry_point("decide_sequence")

    # Flow chính
    workflow.add_edge("decide_sequence", "runner")

    # Nếu còn step → quay lại runner
    # Nếu hết step → sang notion_log
    workflow.add_conditional_edges(
        "runner",
        lambda state: (
            "runner"
            if state["status"]["step"] < len(state["status"]["sequence"])
            else "finalize"
        )
    )

    # Final chain
    workflow.add_edge("finalize", END)

    return workflow
