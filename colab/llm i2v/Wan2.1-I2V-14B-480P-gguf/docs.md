QUY TRÌNH THỰC HIỆN HOÀN CHỈNHGiai đoạn A: Thiết lập Môi trường ComfyUIMở Colab và Chọn GPU:Mở Notebook Colab: comfyui_colab_with_manager.ipynbChọn T4 GPU (Runtime $\rightarrow$ Change runtime type).Chạy tất cả các ô code trong Notebook này (đặc biệt là ô khởi động ComfyUI cuối cùng) và mở giao diện web.Cài đặt Custom Nodes Bắt buộc (Qua Manager):Trong giao diện web ComfyUI, mở Manager.Chọn Install Custom Nodes.Tìm và cài đặt hai node:ComfyUI-GGUFComfyUI-VideoHelperSuiteKhởi động lại ComfyUI: Dừng cell đang chạy trong Colab và chạy lại cell đó để các node được áp dụng.Giai đoạn B: Tải Mô hình Wan 2.1 GGUFDừng ComfyUI: Đảm bảo bạn đã dừng cell đang chạy ComfyUI (bấm nút dừng hoặc Interrupt Execution).Dán và Chạy Code Tải File: Tạo một ô code MỚI trong Notebook Colab của bạn, dán toàn bộ đoạn code tải file GGUF Wan 2.1 bạn đã cung cấp vào đó, và chạy ô code này.(Đoạn code bạn cung cấp là chính xác và sẽ tải 4 file: UNet GGUF, VAE, Text Encoder, và Clip Vision vào đúng vị trí.)Python# @title Tải đầy đủ các thành phần Wan 2.1 GGUF (480P)
%cd /content/ComfyUI/
!apt -y install -qq aria2 ffmpeg # Đảm bảo có aria2

# --- 1. Tải UNet GGUF (Diffusion Model - Kích thước lớn nhất, ~10 GB) ---

# Chọn bản 480P Q4_0 để tối ưu cho T4

GGUF_MODEL = "wan2.1-i2v-14b-480p-Q4_0.gguf"
GGUF_URL = f"https://huggingface.co/city96/Wan2.1-I2V-14B-480P-gguf/resolve/main/{GGUF_MODEL}"

# Lưu vào: ComfyUI/models/unet

print(f"Đang tải UNet GGUF: {GGUF_MODEL}. Quá trình này sẽ mất vài phút...")
!aria2c --console-log-level=error -c -x 16 -s 16 -k 1M $GGUF_URL -d /content/ComfyUI/models/unet -o $GGUF_MODEL

# --- 2. Tải VAE (Video AutoEncoder) ---

VAE_FILE = "wan_2.1_vae.safetensors"
VAE_URL = "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors"

# Lưu vào: ComfyUI/models/vae

print(f"Đang tải VAE: {VAE_FILE}")
!aria2c --console-log-level=error -c -x 16 -s 16 -k 1M $VAE_URL -d /content/ComfyUI/models/vae -o $VAE_FILE

# --- 3. Tải Text Encoder (UMT5-XXL) ---

TEXT_ENCODER = "umt5_xxl_fp16.safetensors"
TEXT_URL = "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp16.safetensors"

# Lưu vào: ComfyUI/models/clip

print(f"Đang tải Text Encoder: {TEXT_ENCODER}")
!aria2c --console-log-level=error -c -x 16 -s 16 -k 1M $TEXT_URL -d /content/ComfyUI/models/clip -o $TEXT_ENCODER

# --- 4. Tải Clip Vision Image Encoder (Clip ViT-L-14) ---

CLIP_VISION = "clip_vision_h.safetensors"

# Sử dụng liên kết chính xác đã xác minh

CLIP_VISION_URL_CORRECT = "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors"

# Lưu vào: ComfyUI/models/clip_vision

print(f"Đang tải Clip Vision chính xác: {CLIP_VISION}")
!aria2c --console-log-level=error -c -x 16 -s 16 -k 1M "$CLIP_VISION_URL_CORRECT" -d /content/ComfyUI/models/clip_vision -o "$CLIP_VISION"

print("\n--- Đã tải xong tất cả các thành phần. Vui lòng chạy lại ComfyUI để tiếp tục. ---")
Giai đoạn C: Chạy Workflow Thử nghiệmTải Workflow JSON: Tải file wan_2.1_i2v_gguf.json về máy tính của bạn (từ liên kết Patreon đã cung cấp).Khởi động lại ComfyUI: Chạy lại cell khởi động ComfyUI và mở giao diện web mới.Tải Workflow: Kéo và thả tệp .json đó vào giao diện ComfyUI.Cấu hình: Đảm bảo các node GGUFLoader, VAELoader, và CLIPLoader đã tự động chọn các file bạn vừa tải xuống. Tải ảnh đầu vào và nhập prompt của bạn.Tạo Video: Nhấn Queue Prompt và chờ Wan 2.1 I2V GGUF tạo ra video so sánh của bạn.

Bước 2: Khởi động lại ComfyUI và Hoàn tất Thử nghiệm
Kiểm tra Status: Đảm bảo ô code trên chạy xong với kết quả (OK).

Khởi động lại ComfyUI: Dừng cell ComfyUI cũ và chạy lại cell đó.

Tải Workflow và Chạy: Tải Workflow JSON vào giao diện web. Tất cả các file mô hình cần thiết đã có trong thư mục, bao gồm cả clip_vision_h.safetensors vừa được tải.

============================================================================
web: https://www.patreon.com/posts/comfyui-workflow-129163468
video: https://www.youtube.com/watch?v=-JE1tt_guGE
git: https://github.com/city96/ComfyUI-GGUF
huggingface: https://huggingface.co/city96/Wan2.1-I2V-14B-480P-gguf
============================================================================
