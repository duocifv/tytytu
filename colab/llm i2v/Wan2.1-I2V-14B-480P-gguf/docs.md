QUY TRÌNH THỰC HIỆN HOÀN CHỈNHGiai đoạn A: Thiết lập Môi trường ComfyUIMở Colab và Chọn GPU:Mở Notebook Colab: comfyui_colab_with_manager.ipynbChọn T4 GPU (Runtime $\rightarrow$ Change runtime type).Chạy tất cả các ô code trong Notebook này (đặc biệt là ô khởi động ComfyUI cuối cùng) và mở giao diện web.Cài đặt Custom Nodes Bắt buộc (Qua Manager):Trong giao diện web ComfyUI, mở Manager.Chọn Install Custom Nodes.Tìm và cài đặt hai node:ComfyUI-GGUFComfyUI-VideoHelperSuiteKhởi động lại ComfyUI: Dừng cell đang chạy trong Colab và chạy lại cell đó để các node được áp dụng.Giai đoạn B: Tải Mô hình Wan 2.1 GGUFDừng ComfyUI: Đảm bảo bạn đã dừng cell đang chạy ComfyUI (bấm nút dừng hoặc Interrupt Execution).Dán và Chạy Code Tải File: Tạo một ô code MỚI trong Notebook Colab của bạn, dán toàn bộ đoạn code tải file GGUF Wan 2.1 bạn đã cung cấp vào đó, và chạy ô code này.(Đoạn code bạn cung cấp là chính xác và sẽ tải 4 file: UNet GGUF, VAE, Text Encoder, và Clip Vision vào đúng vị trí.)Python# @title Tải đầy đủ các thành phần Wan 2.1 GGUF (480P)
%cd /content/ComfyUI/
!apt -y install -qq aria2 ffmpeg # Đảm bảo có aria2

Cài đặt Custom Nodes Bắt buộc (Qua Manager):
Trong giao diện web ComfyUI, mở Manager.
Chọn Install Custom Nodes.

# --- Tìm và cài đặt hai node:

# ComfyUI-GGUF

# ComfyUI-VideoHelperSuite

# ComfyUI-RealESRGAN_Upscaler

# ComfyUI_yanc

# ComfyUI Frame Interpolation

# ComfyUI Impact Pack

# ComfyUI Impact Subpack

# ---

# ComfyUI-Easy-Use - del

mội suy nội dung giữa 2 ảnh:
https://github.com/Fannovel16/ComfyUI-Frame-Interpolation?tab=readme-ov-file

Khởi động lại ComfyUI: Dừng cell đang chạy trong Colab và chạy lại cell đó để các node được áp dụng.

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

⚙️ --async-offload
👉 Dịch: Tự động dỡ (offload) dữ liệu từ GPU sang CPU khi GPU gần đầy.

⚙️ --dont-upcast-attention
👉 Dịch: Không nâng độ chính xác (precision) của attention lên FP32.

⚡ 3 CÁCH GIẢM LAG, GIẢM THỜI GIAN CÀI COMFYUI TRONG COLAB
🧩 Cách 1 – Tạo "snapshot" (đóng gói sẵn toàn bộ môi trường)

Sau khi bạn cài xong và chạy ổn ComfyUI:

!tar -czf comfyui_env.tar.gz /usr/local/lib/python3.12/dist-packages /content/ComfyUI

→ tải file comfyui_env.tar.gz về (khoảng 2–3 GB).
Lần sau chỉ cần:

!tar -xzf comfyui_env.tar.gz -C /

→ môi trường chạy ngay, không cần pip install gì nữa.

⏱ Tiết kiệm: từ 15–20 phút → còn ~1 phút load.

1️⃣ Tạo giọng nói (voice.wav)
Tool Offline / Online Colab khả thi? Notes
Bark TTS (multi-lang) Offline ✅ Có thể chạy Model nhẹ, hỗ trợ tiếng Việt
VietTTS / VITS Offline ✅ Có thể chạy Chạy bằng PyTorch, GPU Colab ok
ElevenLabs Online API ✅ Có thể chạy Gửi request API, cần internet và API key
Coqui TTS Offline ✅ Có thể chạy Community model có tiếng Việt
Tortoise-TTS Offline ✅ Có thể chạy Tiếng Việt đọc lệch, không khuyến nghị

💡 Kết luận: Tất cả đều chạy nổi trên Colab, trừ Tortoise-TTS tiếng Việt chưa chuẩn.

2️⃣ Tạo video nhân vật (ComfyUI)

Colab: ✅ Có thể chạy

Yêu cầu: GPU (T4, A100)

Output: video video.mp4 từ frames / AI model (WanAI I2V, AnimateDiff…)

3️⃣ Lip sync với Wav2Lip

Input: video.mp4 + voice.wav

Output: final_lipsync.mp4

Colab: ✅ Chạy mượt với GPU

Lưu ý: Wav2Lip chỉ lip sync 1 khuôn mặt chính

4️⃣ (Tùy chọn) DeepFaceLab (swap face)

Colab: ⚠️ Chạy được nhưng rất nặng, training lâu

Khuyến nghị:

Nếu chỉ swap 1 video ngắn → có thể chạy

Video dài / nhiều khuôn mặt → nên dùng local PC mạnh hơn

🔹 Kết luận workflow trên Colab

TTS (Bark / VietTTS / Coqui / ElevenLabs) → voice.wav ✅

ComfyUI → tạo video nhân vật ✅

Wav2Lip → sync môi với voice.wav ✅

DeepFaceLab → nếu swap face thì nặng, nhưng video ngắn chạy nổi ⚠️

Như vậy, tất cả bước chính chạy nổi trên Colab, trừ DeepFaceLab cho video dài hoặc nhiều nhân vật thì hơi nặng, cần máy mạnh hơn.
