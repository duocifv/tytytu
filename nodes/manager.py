from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from chains.manager_chain import BlogContext, BlogState, analyze_requirements, interpret_and_standardize
from services.notion_service import NotionService

async def run_blog_workflow(notion: NotionService):
    # Khởi tạo Context và Runtime
    ctx = BlogContext(notion=notion)
    runtime = Runtime(ctx)

    # Khởi tạo StateGraph
    graph = StateGraph(BlogState, context_schema=BlogContext)
    graph.add_node("analyze_requirements", analyze_requirements)
    graph.add_node("interpret_and_standardize", interpret_and_standardize)
    # Thêm các Node khác (research_strategy, idea_scenario, ...) tương tự

    # Thiết lập Entry và Finish Points
    graph.set_entry_point("analyze_requirements")
    graph.set_finish_point("interpret_and_standardize")

    # Biên dịch và chạy Graph
    app = graph.compile()
    await app.invoke({})

    print("✅ Workflow completed")
