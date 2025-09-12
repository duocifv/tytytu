"""
Luồng xử lý tương tác chat chính của ứng dụng.
Xử lý tin nhắn người dùng, phân tích ý định và tạo phản hồi phù hợp.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from prefect import flow, get_run_logger
from tasks import phan_tich_y_dinh, tao_phat_bieu, thuc_thi_cong_cu, truy_van_du_lieu

@dataclass
class PhanHoi:
    """
    Lớp đóng gói phản hồi từ chatbot
    
    Thuộc tính:
        noi_dung: Nội dung phản hồi
        thanh_cong: Trạng thái xử lý (True/False)
        metadata: Thông tin bổ sung (tùy chọn)
    """
    noi_dung: str
    thanh_cong: bool = True
    metadata: Optional[Dict[str, Any]] = None

@flow(name="luong-chat")
async def chat_flow(cau_hoi: str, session_id: Optional[str] = None) -> PhanHoi:
    """
    Luồng xử lý chính cho mỗi tin nhắn từ người dùng
    
    Quy trình:
    1. Phân tích ý định người dùng
    2. Thực thi công cụ hoặc tìm kiếm thông tin
    3. Tạo phản hồi phù hợp
    
    Args:
        cau_hoi: Nội dung câu hỏi từ người dùng
        session_id: ID phiên làm việc (nếu có)
        
    Returns:
        PhanHoi: Đối tượng chứa phản hồi và metadata
    """
    logger = get_run_logger()
    logger.info(f"🟢 Bắt đầu xử lý câu hỏi: {cau_hoi[:50]}...")
    
    try:
        # Bước 1: Phân tích ý định
        logger.info("🔍 Phân tích ý định người dùng...")
        y_dinh = await phan_tich_y_dinh(cau_hoi)
        logger.info(f"✅ Ý định đã xác định: {y_dinh}")
        
        # Bước 2: Xử lý dựa trên ý định
        if y_dinh == "truy_van_du_lieu":
            logger.info("🔎 Truy vấn cơ sở dữ liệu...")
            du_lieu = await truy_van_du_lieu(cau_hoi)
            context = "\n".join(du_lieu) if du_lieu else ""
            phan_hoi_cong_cu = ""
        else:
            logger.info(f"⚙️ Đang thực thi công cụ: {y_dinh}")
            phan_hoi_cong_cu = await thuc_thi_cong_cu(y_dinh, {"truy_van": cau_hoi})
            context = ""
        
        # Bước 3: Tạo phản hồi
        logger.info("💭 Tạo phản hồi...")
        phan_hoi = await tao_phat_bieu(
            cau_hoi=cau_hoi,
            nguyen_canh=context,
            phan_hoi_cong_cu=phan_hoi_cong_cu
        )
        
        logger.info("✅ Xử lý hoàn tất")
        return PhanHoi(
            noi_dung=phan_hoi,
            metadata={
                "y_dinh": y_dinh,
                "su_dung_nguyen_canh": bool(context),
                "session_id": session_id
            }
        )
        
    except Exception as e:
        loi = str(e)
        logger.error(f"❌ Lỗi: {loi}")
        return PhanHoi(
            noi_dung=f"Xin lỗi, tôi gặp lỗi: {loi}",
            thanh_cong=False,
            metadata={"loi": loi, "session_id": session_id}
        )

# Chạy thử
if __name__ == "__main__":
    import asyncio
    
    async def chay_thu():
        """Chạy thử luồng chat với câu hỏi mẫu"""
        mau_cau_hoi = [
            "Thời tiết hôm nay thế nào?",
            "1 + 1 bằng mấy?",
            "Tỷ giá USD hôm nay"
        ]
        
        for cau_hoi in mau_cau_hoi:
            print(f"\n👤 Hỏi: {cau_hoi}")
            ket_qua = await chat_flow(cau_hoi)
            print(f"🤖 Đáp: {ket_qua.noi_dung}")
    
    asyncio.run(chay_thu())
