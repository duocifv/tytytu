"""
Các tác vụ làm việc với cơ sở dữ liệu vector.
Sử dụng ChromaDB để lưu trữ và tìm kiếm văn bản dạng vector.
"""

from prefect import task, get_run_logger
from typing import List, Optional, Dict, Any
import chromadb

# Khởi tạo client ChromaDB (lưu DB tại ./chroma_db)
chroma_client = chromadb.PersistentClient(path="./chroma_db")


@task(name="truy-van-du-lieu")
async def truy_van_du_lieu(cau_hoi: str, top_k: int = 3) -> List[str]:
    """
    Tìm kiếm tài liệu liên quan từ cơ sở dữ liệu vector.
    """
    logger = get_run_logger()
    try:
        logger.info(f"🔍 Đang tìm kiếm {top_k} tài liệu liên quan...")

        # Lấy collection (tạo mới nếu chưa tồn tại)
        collection = chroma_client.get_or_create_collection(name="knowledge_base")

        # Tìm kiếm tài liệu tương đồng
        results = collection.query(
            query_texts=[cau_hoi],
            n_results=top_k
        )

        # Trích xuất nội dung từ kết quả
        documents = results.get("documents", [[]])[0]
        logger.info(f"✅ Tìm thấy {len(documents)} tài liệu liên quan")

        return documents

    except Exception as e:
        logger.error(f"❌ Lỗi khi truy vấn dữ liệu: {str(e)}")
        return []


@task(name="luu-tai-lieu")
def luu_tai_lieu(van_ban: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Lưu trữ tài liệu vào cơ sở dữ liệu vector.
    """
    logger = get_run_logger()
    try:
        logger.info("💾 Đang lưu tài liệu mới...")

        # Lấy collection (tạo mới nếu chưa tồn tại)
        collection = chroma_client.get_or_create_collection(name="knowledge_base")

        # Sinh ID mới an toàn (dựa trên tổng số ID đang có)
        existing = collection.get()
        next_id = f"doc_{len(existing.get('ids', [])) + 1}"

        # Lưu tài liệu
        collection.upsert(
            documents=[van_ban],
            metadatas=[metadata or {}],
            ids=[next_id]
        )

        logger.info(f"✅ Đã lưu tài liệu với ID: {next_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Lỗi khi lưu tài liệu: {str(e)}")
        return False
