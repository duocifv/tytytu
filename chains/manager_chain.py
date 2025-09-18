import asyncio
from dataclasses import dataclass
from langgraph.graph import StateGraph, END
from langgraph.runtime import Runtime
from typing_extensions import TypedDict
from services.notion_service import NotionService

# Định nghĩa Context
@dataclass
class BlogContext:
    task_id: str = "Blog Task 1"

# Định nghĩa State
class BlogState(TypedDict):
    Topic: str
    Audience: str
    Guideline: dict
    Keywords: list
    Outline: list

# Các Node Functions
async def analyze_requirements(state: BlogState, runtime: Runtime[BlogContext]):
    print("📌 Phân tích yêu cầu...")
    await asyncio.sleep(1)
    state.update({"Topic": "AI và tương lai công việc", "Audience": "Developer & PM"})
    await runtime.context.notion.create_task(runtime.context.task_id)
    await runtime.context.notion.update_task(runtime.context.task_id, state)

async def interpret_and_standardize(state: BlogState, runtime: Runtime[BlogContext]):
    print("📑 Chuẩn hóa...")
    await asyncio.sleep(1)
    state.update({"Guideline": {"tone": "Thân thiện", "length": "1000-1500 từ"}})
    await runtime.context.notion.update_task(runtime.context.task_id, {"Guideline": state["Guideline"]})

# Các Node khác (research_strategy, idea_scenario, ...) tương tự
