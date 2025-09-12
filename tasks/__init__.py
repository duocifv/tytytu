"""
Gói chứa các task cho hệ thống Chatbot AI.

Bao gồm các tác vụ xử lý ngôn ngữ, tìm kiếm thông tin và tương tác với các công cụ.
Tasks package for the application.
"""

# Import tasks from modules
from .llm_tasks import analyze_intent, generate_response
from .tool_tasks import (
    execute_tool, 
    get_available_tools, 
    process_with_agent,
    agent_executor as get_tool_agent,
    TOOLS,
    TOOL_HANDLERS,
    TOOL_NAME_TO_MODEL
)
from .vector_tasks import search_knowledge_base, save_document, delete_document

# For backward compatibility
phan_tich_y_dinh = analyze_intent
tao_phat_bieu = generate_response
thuc_thi_cong_cu = execute_tool
lay_danh_sach_cong_cu = get_available_tools
truy_van_du_lieu = search_knowledge_base
luu_tai_lieu = save_document
xoa_tai_lieu = delete_document

# Xuất các hàm chính để sử dụng trong các luồng
__all__ = [
    'phan_tich_y_dinh',
    'tao_phat_bieu',
    'thuc_thi_cong_cu',
]
