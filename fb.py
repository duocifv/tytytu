from services.facebook_service import FacebookPipeline

if __name__ == "__main__":
    fb = FacebookPipeline()

    # Nội dung bài muốn đăng
    message = "🚀 Test post tự động từ FacebookService"
    link = "https://example.com"  # nếu muốn đính kèm link, else None

    # Đăng bài
    result = fb.post_message(message, link=link)

    # In kết quả trả về từ Facebook API
    print("\n📌 Post Result:")
    print(result)

    # Lấy info Page
    info = fb.get_page_info()
    print("\n📌 Page Info:")
    print(info)
