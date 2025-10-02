# run_fb_debug.py
import os
import json
from services.facebook_service import FacebookPipeline

def main():
    # Khởi tạo FacebookPipeline
    fb = FacebookPipeline()

    # Path tới video bạn muốn upload
    video_path = "generated_images/v_3deb.mp4"

    # Kiểm tra video tồn tại
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        print("❌ Video không tồn tại hoặc rỗng:", video_path)
        return


    # Nội dung gốc
    title = '''ôi khi, những gánh nặng lớn nhất lại đến từ chính suy nghĩ của chúng ta. Chúng ta lo lắng về nhữn'''

    description = '''Đôi khi, những gánh nặng lớn nhất lại đến từ chính suy nghĩ của chúng ta. Chúng ta lo lắng về những điều chưa xảy ra, tạo ra những kịch bản tồi tệ nhất trong tâm trí, và rồi tự mình chịu đựng. Seneca từng nói rất đúng: "Chúng ta thường đau khổ nhiều hơn trong tưởng tượng so với thực tế." Hãy thử dừng lại một chút, hít thở sâu và tự hỏi: Liệu điều mình đang lo lắng có thật sự tồi tệ đến vậy không, hay chỉ là do tâm trí đang phóng đại? Buông bỏ bớt những suy nghĩ tiêu cực, tập trung vào hiện tại và những gì chúng ta có thể kiểm soát. Bạn sẽ thấy nhẹ nhõm hơn rất nhiều! ✨ #TuDuyTichCuc #HienTai #BuongBoLoLang'''

    # Cắt nội dung theo ký tự
    fb_title = title[:255] 

    # Upload video (tự động chọn direct/resumable theo kích thước)
    result = fb.post_video(video_path, title=fb_title, description=description)

    # In kết quả chi tiết
    print("Kết quả upload video:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
