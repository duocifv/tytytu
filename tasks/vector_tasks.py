"""
Vector database tasks using ChromaDB.

This module provides functions for storing and retrieving documents
using vector similarity search.
"""
from prefect import task, get_run_logger
from typing import List, Optional, Dict, Any
import chromadb
import uuid

# Initialize ChromaDB client (stores data in ./chroma_db)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

@task(name="search-knowledge-base")
async def search_knowledge_base(
    query: str, 
    top_k: int = 3,
    collection_name: str = "knowledge_base"
) -> List[str]:
    """
    Tìm kiếm tài liệu liên quan từ cơ sở dữ liệu vector.
    
    Args:
        query: Câu truy vấn tìm kiếm
        top_k: Số lượng kết quả trả về
        collection_name: Tên collection trong ChromaDB
        
    Returns:
        Danh sách các tài liệu liên quan
    """
    logger = get_run_logger()
    try:
        logger.info(f"[Vector] Đang tìm kiếm {top_k} tài liệu liên quan...")

        # Lấy collection (tạo mới nếu chưa tồn tại)
        collection = chroma_client.get_or_create_collection(name=collection_name)

        # Tìm kiếm tài liệu tương đồng
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )

        # Trích xuất nội dung từ kết quả
        documents = results.get("documents", [[]])[0]
        logger.info(f"[Vector] Tìm thấy {len(documents)} tài liệu liên quan")

        return documents

    except Exception as e:
        logger.error(f"[Vector] Lỗi khi tìm kiếm: {str(e)}", exc_info=True)
        return []

@task(name="save-document")
async def save_document(
    content: str, 
    metadata: Optional[Dict[str, Any]] = None,
    collection_name: str = "knowledge_base"
) -> str:
    """
    Lưu trữ tài liệu vào cơ sở dữ liệu vector.
    
    Args:
        content: Nội dung tài liệu cần lưu
        metadata: Metadata của tài liệu
        collection_name: Tên collection trong ChromaDB
        
    Returns:
        ID của tài liệu đã lưu, hoặc chuỗi rỗng nếu thất bại
    """
    logger = get_run_logger()
    try:
        logger.info("[Vector] Đang lưu tài liệu mới...")

        # Lấy collection (tạo mới nếu chưa tồn tại)
        collection = chroma_client.get_or_create_collection(name=collection_name)

        # Tạo ID duy nhất cho tài liệu
        doc_id = f"doc_{str(uuid.uuid4())[:8]}"

        # Lưu tài liệu
        collection.upsert(
            documents=[content],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )

        logger.info(f"[Vector] Đã lưu tài liệu với ID: {doc_id}")
        return doc_id

    except Exception as e:
        logger.error(f"[Vector] Lỗi khi lưu tài liệu: {str(e)}", exc_info=True)
        return ""

@task(name="delete-document")
async def delete_document(
    doc_id: str,
    collection_name: str = "knowledge_base"
) -> bool:
    """
    Xóa tài liệu khỏi cơ sở dữ liệu vector.
    
    Args:
        doc_id: ID của tài liệu cần xóa
        collection_name: Tên collection trong ChromaDB
        
    Returns:
        True nếu xóa thành công, False nếu thất bại
    """
    logger = get_run_logger()
    try:
        logger.info(f"[Vector] Đang xóa tài liệu {doc_id}...")
        
        collection = chroma_client.get_collection(name=collection_name)
        collection.delete(ids=[doc_id])
        
        logger.info(f"[Vector] Đã xóa tài liệu {doc_id}")
        return True
        
    except Exception as e:
        logger.error(f"[Vector] Lỗi khi xóa tài liệu: {str(e)}", exc_info=True)
        return False
