"""
telegram_flow.py

Telegram Message Processing Flow

Main processing flow for Telegram messages, including:
1. User intent analysis
2. Relevant information retrieval
3. Tool/agent processing
4. Response generation
"""
from typing import Dict, Any, Optional, Union, List
import logging
from prefect import flow, get_run_logger

# Import tasks
from tasks.llm_tasks import analyze_intent, generate_response
from tasks.tool_tasks import process_with_agent
from tasks.vector_tasks import search_knowledge_base

@flow(name="telegram-message-flow")
async def process_message_flow(
    message: str, 
    user_id: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Xử lý tin nhắn người dùng và tạo phản hồi phù hợp.
    
    Args:
        message: Nội dung tin nhắn từ người dùng
        user_id: ID người dùng trên Telegram
        session_id: ID phiên tùy chọn để theo dõi hội thoại
        
    Returns:
        Dict chứa nội dung phản hồi và metadata
    """
    logger = get_run_logger()
    logger.info(f"🔄 Bắt đầu xử lý tin nhắn từ người dùng {user_id}")
    
    try:
        # Bước 1: Phân tích ý định
        logger.info("🔍 Đang phân tích ý định người dùng...")
        intent = await analyze_intent(message)
        logger.info(f"✅ Đã xác định ý định: {intent}")
        
        # Bước 2: Lấy ngữ cảnh nếu cần
        logger.debug("🌐 Đang thu thập ngữ cảnh phù hợp...")
        context = await _get_context(message, intent, logger)
        if context:
            logger.info(f"📚 Đã tìm thấy {len(context.split('\n'))} mục ngữ cảnh phù hợp")
        
        # Bước 3: Xử lý với agent/công cụ
        logger.info("⚙️ Đang xử lý yêu cầu với agent...")
        tool_result = await process_with_agent({
            "tool_name": intent,
            "content": message
        })
        logger.info(f"tool_result: {tool_result}")
        # 1) Nếu agent đã tổng hợp reply (LLM synthesize) -> trả ngay
        reply = tool_result.get("reply")
        if reply:
            logger.info("Agent trả về reply đã được tổng hợp, trả cho user.")
            return reply

        # 2) Nếu có tool_results -> lấy kết quả đầu tiên để build response qua tao_phat_bieu
        tool_results = tool_result.get("tool_results", [])
        if tool_results:
            first = tool_results[0]
            dispatch = first.get("dispatch", {})

            if dispatch.get("ok"):
                # dispatch result là dict (handler trả về dict)
                tool_output_obj = dispatch.get("result", {})
                # convert to string (chuỗi/gợi ý) để đưa vào tao_phat_bieu
                tool_output = (
                    tool_output_obj.get("summary")
                    if isinstance(tool_output_obj, dict) and tool_output_obj.get("summary")
                    else str(tool_output_obj)
                )
            else:
                # handler lỗi -> truyền thông báo lỗi
                tool_output = f"[Tool error] {dispatch.get('error', 'Unknown error')}"

            logger.info(f"Using first tool result to build reply: {tool_output}")

            return await _generate_response(
                message=message,
                context=context,
                tool_result=tool_output,
                logger=logger
            )

        # 3) Fallback: không có reply lẫn tool result
        logger.info("No reply and no tool results -> fallback response.")
        return await _generate_response(
            message=message,
            context=context,
            tool_result="Không có kết quả từ công cụ.",
            logger=logger
        )
        # if tool_result:
        #     logger.debug(f"🔧 Kết quả từ công cụ: {str(tool_result)[:200]}...")
        
        # # Bước 4: Tạo và trả về phản hồi
        # logger.info("💬 Đang tạo phản hồi...")
        # response = await _generate_response(
        #     message=message,
        #     context=context,
        #     tool_result=tool_result,
        #     logger=logger
        # )
        
        # logger.info(f"✅ Hoàn thành xử lý tin nhắn cho user {user_id}")
        # return response
        
    except Exception as e:
        logger.critical(f"❌ LỖI NGHIÊM TRỌNG khi xử lý tin nhắn: {str(e)}", exc_info=True)
        return "❌ Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau. "

async def _get_context(
    message: str, 
    intent: str, 
    logger: logging.Logger
) -> str:
    """
    Truy xuất ngữ cảnh từ cơ sở tri thức nếu cần.
    
    Args:
        message: Tin nhắn của người dùng
        intent: Ý định đã xác định
        logger: Đối tượng logger
        
    Returns:
        str: Ngữ cảnh đã tìm thấy hoặc chuỗi rỗng
    """
    if intent == "search_knowledge_base":
        logger.info("🔍 Đang tìm kiếm thông tin liên quan...")
        try:
            results = await search_knowledge_base(message)
            if results:
                logger.info(f"✅ Đã tìm thấy {len(results)} tài liệu liên quan")
                return "\n".join(results)
            else:
                logger.warning("⚠️ Không tìm thấy thông tin liên quan")
        except Exception as e:
            logger.error(f"❌ Lỗi khi tìm kiếm cơ sở tri thức: {e}")
            logger.debug(f"Chi tiết lỗi: {str(e)}", exc_info=True)
    else:
        logger.debug("⏩ Bỏ qua tìm kiếm ngữ cảnh do không cần thiết")
    return ""

async def _generate_response(
    message: str,
    context: str,
    tool_result: Dict[str, Any],
    logger: logging.Logger
) -> str:
    """
    Tạo phản hồi dựa trên kết quả từ công cụ và ngữ cảnh.
    
    Args:
        message: Tin nhắn gốc từ người dùng
        context: Ngữ cảnh từ cơ sở tri thức
        tool_result: Kết quả từ quá trình xử lý công cụ/agent
        logger: Đối tượng logger
        
    Returns:
        str: Văn bản phản hồi được tạo
    """
    logger.info("💬 Bắt đầu tạo phản hồi...")
    
    try:
        # Trích xuất kết quả từ công cụ
        logger.debug("🔧 Đang trích xuất dữ liệu từ công cụ...")
        tool_output = _extract_tool_output(tool_result, logger)
        if tool_output:
            logger.debug(f"📋 Dữ liệu từ công cụ: {tool_output[:200]}...")
        
        # Tạo phản hồi sử dụng LLM
        logger.info("🧠 Đang tạo phản hồi với mô hình ngôn ngữ...")
        response = await generate_response(
            question=message,
            context=context,
            tool_output=tool_output
        )
        
        if not response:
            logger.warning("⚠️ Không thể tạo phản hồi từ mô hình ngôn ngữ")
            return "Xin lỗi, tôi không thể tạo phản hồi phù hợp vào lúc này."
            
        logger.info("✅ Đã tạo phản hồi thành công")
        return response
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi tạo phản hồi: {e}", exc_info=True)
        return "Xin lỗi, đã xảy ra lỗi khi tạo phản hồi. Vui lòng thử lại sau."

def _extract_tool_output(tool_result: Any, logger: logging.Logger = None) -> str:
    """
    Trích xuất thông tin từ kết quả công cụ/agent.
    
    Args:
        tool_result: Kết quả thô từ công cụ/agent
        logger: Đối tượng logger (tùy chọn)
        
    Returns:
        str: Kết quả đã được trích xuất dưới dạng chuỗi
    """
    def _log(level: str, message: str):
        if logger:
            getattr(logger, level)(message)
    
    if not tool_result:
        _log("debug", "⏩ Không có dữ liệu từ công cụ để trích xuất")
        return ""
    
    try:
        if isinstance(tool_result, str):
            _log("debug", "📄 Kết quả là chuỗi, trả về trực tiếp")
            return tool_result
        elif isinstance(tool_result, dict):
            _log("debug", "📊 Kết quả là dictionary, trích xuất trường output/response")
            return str(tool_result.get("output", tool_result.get("response", "")))
        elif hasattr(tool_result, "__dict__"):
            _log("debug", "🔍 Kết quả là đối tượng, chuyển đổi thành dictionary")
            return str(tool_result.__dict__)
        else:
            _log("debug", f"🔄 Chuyển đổi kết quả sang chuỗi: {type(tool_result)}")
            return str(tool_result)
    except Exception as e:
        _log("error", f"❌ Lỗi khi trích xuất kết quả công cụ: {e}")
        return ""
