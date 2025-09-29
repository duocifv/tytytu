from typing import TypedDict, List, Dict, Literal, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dataclasses import dataclass
from typing import List, Optional


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






@dataclass
class BaseRelationNested:
    Opposite: Optional[List["BaseRelation"]] = None
    Transform: Optional[List["BaseRelation"]] = None
    Ally: Optional[List["BaseRelation"]] = None
    Support: Optional[dict] = None  # {'in': List[BaseRelation], 'out': List[BaseRelation]}

@dataclass
class BaseRelation:
    id: int
    name: str
    bits: str
    trigram: str
    element: str
    weight: Optional[float] = None
    relation: Optional[str] = None
    incoming: Optional[bool] = None
    source: Optional[int] = None
    target: Optional[int] = None
    relations: Optional[BaseRelationNested] = None

@dataclass
class Base:
    bitstring: str
    id: int
    name: str
    bits: str
    relations: BaseRelationNested

@dataclass
class Transformed:
    bitstring: str
    id: int
    name: str
    bits: str
    relations: BaseRelationNested

@dataclass
class FullDailyData:
    # từ data_analysis_node
    thien: str
    dia: str
    nhan: str
    key_event: str

    # từ create_daily_node
    node_id: str
    timestamp: str
    Thien: str
    Dia: str
    Nhan: str
    KeyEvent: str
    llm_summary: str
    llm_key_event_effect: str
    scores: dict  # {'H1': int, 'H2': int, 'H3': int, 'H4': int, 'H5': int, 'H6': int}
    bits_h1_h6: List[int]
    moving_flags: List[bool]
    base: Base
    transformed: Transformed

    # từ human_reference_node
    health: str
    finance: str
    psychology: str
    work: str
    trend: str
    note: str



class State(TypedDict):
    """Trạng thái tổng của workflow"""
    messages: List[Message]  # lịch sử hội thoại
    outputs: Outputs         # kết quả
    retries: Dict[str, int]  # số lần retry theo node
    topic: str               # chủ đề
    status: Status           # tiến độ
    daily: FullDailyData