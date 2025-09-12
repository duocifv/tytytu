"""
Luồng xử lý tìm kiếm và tạo phản hồi bằng RAG (Retrieval-Augmented Generation).
Kết hợp tìm kiếm thông tin và tạo phản hồi tự động.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from prefect import flow, get_run_logger
from tasks import truy_van_du_lieu, tao_phat_bieu

@dataclass
class PhanHoiRAG:
    """Lớp đóng gói phản hồi từ RAG"""
    noi_dung: str
    so_luong_nguon: int = 0
    top_k: int = 3
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None

@flow(name="luong-rag")
async def rag_flow(cau_hoi: str, top_k: int = 3, session_id: str = None) -> PhanHoiRAG:
    """
    Xử lý câu hỏi bằng kỹ thuật RAG
    
    Quy trình:
    1. Tìm kiếm tài liệu liên quan
    2. Tổng hợp thông tin và tạo phản hồi
    
    Args:
        cau_hoi: Câu hỏi cần tìm kiếm
        top_k: Số lượng tài liệu cần lấy
        session_id: ID phiên làm việc (nếu có)
        
    Returns:
        PhanHoiRAG: Đối tượng chứa phản hồi và thông tin liên quan
    """
    logger = get_run_logger()
    logger.info(f"🔍 Bắt đầu xử lý RAG cho câu hỏi: {cau_hoi[:50]}...")
    
    try:
        # Bước 1: Tìm kiếm tài liệu liên quan
        logger.info(f"🔎 Đang tìm kiếm {top_k} tài liệu liên quan...")
        tai_lieu = await truy_van_du_lieu(cau_hoi, top_k)
        
        # Bước 2: Tạo phản hồi dựa trên ngữ cảnh
        if tai_lieu:
            context = "\n".join(tai_lieu)
            logger.info(f"✅ Tìm thấy {len(tai_lieu)} tài liệu liên quan")
            
            phan_hoi = await tao_phat_bieu(
                cau_hoi=cau_hoi,
                nguyen_canh=context,
                phan_hoi_cong_cu=""
            )
            
            return PhanHoiRAG(
                noi_dung=phan_hoi,
                so_luong_nguon=len(tai_lieu),
                top_k=top_k,
                session_id=session_id,
                metadata={
                    "ngay_xu_ly": datetime.now().isoformat(),
                    "loai_phuong_thuc": "rag"
                }
            )
        else:
            logger.warning("⚠️ Không tìm thấy tài liệu liên quan")
            return PhanHoiRAG(
                noi_dung="Xin lỗi, tôi không tìm thấy thông tin liên quan.",
                so_luong_nguon=0,
                top_k=top_k,
                session_id=session_id,
                metadata={"loi": "Không có dữ liệu phù hợp"}
            )
            
    except Exception as e:
        loi = str(e)
        logger.error(f"❌ Lỗi khi xử lý RAG: {loi}")
        return PhanHoiRAG(
            noi_dung="Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu.",
            so_luong_nguon=0,
            session_id=session_id,
            metadata={"loi": loi}
        )

# Chạy thử
if __name__ == "__main__":
    import asyncio
    
    async def chay_thu_rag():
        """Chạy thử luồng RAG với câu hỏi mẫu"""
        mau_cau_hoi = [
            "Chatbot là gì?",
            "Cách sử dụng Prefect?",
            "Giới thiệu về LangChain"
        ]
        
        for cau_hoi in mau_cau_hoi:
            print(f"\n🔍 Hỏi: {cau_hoi}")
            ket_qua = await rag_flow(cau_hoi, top_k=2)
            print(f"📚 Số nguồn: {ket_qua.so_luong_nguon}")
            print(f"🤖 Trả lời: {ket_qua.noi_dung[:200]}...")
    
    asyncio.run(chay_thu_rag())
