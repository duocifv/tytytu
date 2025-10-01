# ---------------- Example usage (tối giản) ----------------
from PIL import Image
from services.poster_service import DEFAULT_FONT_URL, generate_poster

if __name__ == "__main__":
    IMAGE_PATH = r"D:\duocnv\tytytu\generated_images\h1.jpg"
    OUTPUT_PATH = r"D:\duocnv\tytytu\generated_images\output_poster_simple.png"

    # mở ảnh
    pil_img = Image.open(IMAGE_PATH)

    # tạo poster
    poster = generate_poster(
        pil_image=pil_img,
        text="Bạn có quyền kiểm soát tâm trí mình – chứ không phải những sự kiện bên ngoài. Hãy nhận thức điều này, và bạn sẽ tìm thấy sức mạnh.",
        author="Marcus Aurelius",
        size=512,
        padding=38,
        font_size=30,
        line_spacing=4,
        brightness=0.6,
        saturation=1.4,
        gradient_alpha=38,
        tone='Warm, serene',  # có thể thử "happy" hoặc "sad"
    )


    # lưu PNG (giữ alpha)
    poster.save(OUTPUT_PATH, format="PNG")
    print("Saved poster to:", OUTPUT_PATH)
