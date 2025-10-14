# canny_generator_resized.py

import cv2
from pathlib import Path
from PIL import Image

# Thư mục chứa ảnh gốc
input_dir = Path("images_original")
# Thư mục lưu ảnh Canny
output_dir = Path("images_canny")
output_dir.mkdir(exist_ok=True)

# Kích thước chuẩn cho ControlNet
target_size = (512, 512)

# Các thông số Canny
threshold1 = 100
threshold2 = 200

# Duyệt tất cả file ảnh phổ biến
for ext in ("*.jpg", "*.jpeg", "*.png"):
    for img_path in input_dir.glob(ext):
        # Đọc ảnh gốc grayscale
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"⚠️ Không đọc được ảnh {img_path.name}")
            continue-

        # Resize về target_size
        img = cv2.resize(img, target_size)

        # Áp dụng Canny
        edges = cv2.Canny(img, threshold1, threshold2)

        # Chuyển sang PIL Image (RGB) để lưu
        canny_img = Image.fromarray(edges).convert("RGB")
        canny_img.save(output_dir / img_path.name)
        print(f"✅ Đã tạo ảnh Canny: {img_path.name}")

print("🎉 Hoàn tất tất cả ảnh!")
