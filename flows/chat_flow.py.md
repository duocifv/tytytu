"""
Main chat interaction flow for the application.

Handles user messages, analyzes intent, and generates appropriate responses.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import logging
from tasks import (
    analyze_intent, 
    generate_response,
    execute_tool,
    search_knowledge_base,
    process_with_agent
)

# Configure logging
logger = logging.getLogger(__name__)

def flow(func):
    """Decorator to maintain compatibility with flow functions"""
    return func

@dataclass
class BotResponse:
    """
    Class representing a bot response.
    
    Attributes:
        content: The response content
        success: Whether the processing was successful
        metadata: Additional metadata (optional)
    """
    content: str
    success: bool = True
    metadata: Optional[Dict[str, Any]] = None

async def chat_flow(
    user_input: str, 
    session_id: Optional[str] = None
) -> BotResponse:
    """
    Main processing flow for each user message.
    
    Process:
    1. Analyze user intent
    2. Execute tools or search for information
    3. Generate appropriate response
    
    Args:
        user_input: The user's message
        session_id: Optional session ID for conversation tracking
        
    Returns:
        BotResponse: Object containing the response and metadata
    """
    logger.info(f"📥 Received message: {user_input} Bắt đầu xử lý câu hỏi: {user_input[:50]}...")
    
    try:
        # Step 1: Analyze intent
        logger.info("[Chat] Đang phân tích ý định...")
        intent = await analyze_intent(user_input)
        logger.info(f"[Chat] Ý định: {intent}")
        
        # Step 2: Process based on intent
        if intent == "search_knowledge_base":
            logger.info("[Chat] Đang tìm kiếm thông tin...")
            search_results = await search_knowledge_base(user_input)
            context = "\n".join(search_results) if search_results else ""
            tool_output = ""
        else:
            # Use agent for other intents
            logger.info(f"[Chat] Đang xử lý với agent: {intent}")
            agent_result = await process_with_agent(user_input)
            
            if agent_result.get("success"):
                tool_output = agent_result.get("response", {})
                context = ""
            else:
                error_msg = agent_result.get("error", "Lỗi không xác định")
                logger.error(f"[Chat] Lỗi khi xử lý với agent: {error_msg}")
                return BotResponse(
                    content="Xin lỗi, tôi gặp khó khăn khi xử lý yêu cầu của bạn.",
                    success=False,
                    metadata={"error": error_msg}
                )
        
        # Step 3: Generate response
        logger.info("[Chat] Đang tạo phản hồi...")
        response = await generate_response(
            question=user_input,
            context=context,
            tool_output=str(tool_output)
        )
        
        return BotResponse(
            content=response,
            success=True,
            metadata={
                "intent": intent,
                "context": context,
                "tool_output": tool_output,
                "session_id": session_id
            }
        )
        
    except Exception as e:
        logger.error(f"[Chat] Lỗi khi xử lý: {e}", exc_info=True)
        return BotResponse(
            content="❌ Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau.",
            success=False,
            metadata={"error": str(e)}
        )

# Test the flow
if __name__ == "__main__":
    import asyncio
    
    async def test_flow():
        """Test the chat flow with sample questions"""
        test_questions = [
            "Thời tiết hôm nay thế nào?",
            "Tìm kiếm thông tin về AI",
            "Tính toán 2 + 2"
        ]
        
        for question in test_questions:
            print(f"\n{'='*50}")
            print(f"Người dùng: {question}")
            
            response = await chat_flow(question)
            print(f"\nBot: {response.content}")
            
            if not response.success:
                print(f"\nLỗi: {response.metadata.get('error', 'Không xác định')}")
    
    asyncio.run(test_flow())
