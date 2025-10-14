import cv2
from PIL import Image

def create_canny(image_path="./cyrielle_ref.webp", save_path="./canny-edge.png"):
    """
    Tạo ảnh Canny edge map từ ảnh gốc (image_path)
    và lưu thành ảnh RGB (3 kênh) tại save_path.
    """
    # Đọc ảnh gốc
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Không tìm thấy ảnh nguồn: {image_path}")
        return

    # Chuyển sang ảnh Canny (phát hiện biên cạnh)
    edges = cv2.Canny(img, 100, 200)

    # Chuyển từ grayscale sang RGB để ControlNet dùng được
    canny_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

    # Lưu kết quả
    Image.fromarray(canny_rgb).save(save_path)
    print("✅ Đã tạo ảnh Canny:", save_path)

if __name__ == "__main__":
    create_canny()
