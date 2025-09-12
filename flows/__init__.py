"""
Flows for the AI Chatbot System.

This package contains all flow definitions for the chatbot system,
including the main chat flow, RAG flow, message flow, and other workflow orchestrations.
"""

from .chat_flow import chat_flow
from .rag_flow import rag_flow
from .telegram_flow import process_message_flow

# For backward compatibility
from .telegram_flow import process_message_flow as xu_ly_tin_nhan

__all__ = [
    "chat_flow",
    "rag_flow",
    "process_message_flow",
    "xu_ly_tin_nhan"  # Keep for backward compatibility
]
