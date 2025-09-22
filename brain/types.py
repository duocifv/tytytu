from typing import TypedDict, List, Dict, Literal, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


# Các bước cố định của pipeline
PipelineStep = Literal["keyword", "research", "insight", "idea", "title", "content", "publish"]

# Union cho messages (LangChain)
Message = Union[HumanMessage, AIMessage, SystemMessage]


class Status(TypedDict, total=False):
    """Thông tin tiến độ workflow"""
    sequence: int         # thứ tự sequence hiện tại
    step: str             # bước hiện tại
    done_nodes: List[str] # các node đã hoàn thành


class Outputs(TypedDict, total=False):
    """Dữ liệu đầu ra của workflow"""
    keyword: List[str]
    research: List[Dict[str, str]]
    insight: List[str]
    idea: List[str]
    title: str
    content: str
    publish: Dict[str, str]


class State(TypedDict):
    """Trạng thái tổng của workflow"""
    messages: List[Message]  # lịch sử hội thoại
    outputs: Outputs         # kết quả
    retries: Dict[str, int]  # số lần retry theo node
    topic: str               # chủ đề
    status: Status           # tiến độ
