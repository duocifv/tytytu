# --- robust import for IPAdapterFaceIDXL ---
import sys, os, importlib.util, types

try:
    from ip_adapter.ip_adapter_faceid import IPAdapterFaceIDXL
    print("✅ Imported IPAdapterFaceIDXL normally")
except Exception as e:
    print("⚠️ Normal import failed:", e)
    candidate = None
    candidate_roots = [
        os.getcwd(),
        "/content",
        "/content/IP-Adapter",
        os.path.join(os.getcwd(), "IP-Adapter")
    ]
    for root in candidate_roots:
        p = os.path.join(root, "ip_adapter", "ip_adapter_faceid.py")
        if os.path.isfile(p):
            candidate = p
            break
    if candidate is None:
        for dirpath, dirnames, filenames in os.walk(os.getcwd()):
            if "ip_adapter_faceid.py" in filenames:
                candidate = os.path.join(dirpath, "ip_adapter_faceid.py")
                break
    if candidate is None:
        raise ModuleNotFoundError("❌ Không tìm thấy ip_adapter_faceid.py")

    print("🔹 Loading from", candidate)
    spec = importlib.util.spec_from_file_location("ip_adapter.ip_adapter_faceid", candidate)
    module = importlib.util.module_from_spec(spec)
    if "ip_adapter" not in sys.modules:
        pkg = types.ModuleType("ip_adapter")
        pkg.__path__ = [os.path.dirname(candidate)]
        sys.modules["ip_adapter"] = pkg
    sys.modules["ip_adapter.ip_adapter_faceid"] = module
    spec.loader.exec_module(module)
    IPAdapterFaceIDXL = getattr(module, "IPAdapterFaceIDXL")
    print("✅ Loaded IPAdapterFaceIDXL via importlib")




from diffusers import StableDiffusionXLPipeline, ControlNetModel
from transformers import CLIPVisionModelWithProjection
import torch
from PIL import Image
import os
from io import BytesIO
from IPython.display import display, Image as IPImage
from diffusers.utils import load_image

# ---- thêm ----
import cv2
from insightface.app import FaceAnalysis


# ----------------------------
# Config & device
# ----------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
print("🔹 Device:", device, " dtype:", dtype)

MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
CONTROLNET_ID = "diffusers/controlnet-canny-sdxl-1.0"
IP_CKPT = "ip-adapter-faceid_sdxl.bin"   # <-- kiểm tra tồn tại file này
REF_IMG_PATH = "./lora20.jpg"
LORA_PATH = "./hinaCreativeLomo.safetensors"
CANNY_PATH = "./canny-edge3.png"

# ----------------------------
# Load main pipeline (base)
# ----------------------------
print("🔹 Loading SDXL base...")
pipe = StableDiffusionXLPipeline.from_pretrained(
    MODEL_ID,
    controlnet=None,
    torch_dtype=dtype
)

pipe.enable_attention_slicing()
pipe.enable_vae_slicing()

# ----------------------------
# Chọn: sử dụng model CPU offload để giảm VRAM (KHÔNG gọi pipe.to(device) sau này)
# ----------------------------
# pipe.enable_model_cpu_offload()
pipe.to("cuda")
print("🔹 Model CPU offload enabled — DO NOT call pipe.to(device) to preserve offloading behavior.")

# Nếu bạn muốn chạy hoàn toàn trên CUDA thay vì offload, đổi lại: comment 2 dòng enable_model_cpu_offload và gọi pipe.to(device)

try:
    if device == "cuda":
        pipe.enable_xformers_memory_efficient_attention()
        print("🔹 xformers enabled")
except Exception as e:
    print("⚠️ xformers not available or failed to enable:", e)

# ----------------------------
# Load controlnet and attach (COMMENTED)
# ----------------------------
# print("🔹 Loading ControlNet (Canny)...")
# controlnet = ControlNetModel.from_pretrained(
#     CONTROLNET_ID,
#     torch_dtype=dtype
# ).to(device)
# pipe.controlnet = controlnet
# print("✅ ControlNet attached to pipeline and moved to", device)

# ----------------------------
# Load LoRA if present (COMMENTED)
# ----------------------------
# if os.path.exists(LORA_PATH):
#     try:
#         print("🔹 Loading LoRA:", LORA_PATH)
#         pipe.load_lora_weights(
#             ".",
#             weight_name=os.path.basename(LORA_PATH),
#             use_peft_backend=True,
#             device_map="auto"
#         )
#         pipe.fuse_lora(lora_scale=0.9)
#         print("✅ LoRA loaded and fused (scale=0.9)")
#     except Exception as e:
#         print("⚠️ Failed to load LoRA:", e)
# else:
#     print("⚠️ No LoRA file found at", LORA_PATH, "- continuing without LoRA.")

# ----------------------------
# Extract FaceID embedding (ROBUST)
# ----------------------------
import gc, numpy as np
from IPython.display import display as _display, Image as _IPImage

# free a bit first
torch.cuda.empty_cache()
gc.collect()

if not os.path.exists(REF_IMG_PATH):
    raise SystemExit(f"❌ Ảnh tham chiếu không tồn tại: {REF_IMG_PATH}")

img_ref = cv2.imread(REF_IMG_PATH)
if img_ref is None:
    raise SystemExit(f"❌ Không đọc được ảnh (file hỏng/định dạng không hỗ trợ): {REF_IMG_PATH}")

print("✅ Ảnh load thành công:", REF_IMG_PATH, "shape:", img_ref.shape)
_debug_tmp = "/content/_debug_ref.jpg"
cv2.imwrite(_debug_tmp, img_ref)
try:
    _display(_IPImage(_debug_tmp))
except Exception:
    pass

# Use CPU provider to avoid ONNX OOM when SDXL artifacts loaded
print("🔹 Extracting FaceID embedding with InsightFace (CPU)...")
faces = []
try:
    app = FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    faces = app.get(img_ref)
    print("  => faces detected:", len(faces))
except Exception as e:
    print("  => InsightFace exception:", repr(e))
    faces = []

# if not found, try smaller det_size or smaller model
if not faces:
    try:
        print("Retry with smaller det_size (320,320)...")
        del app
        gc.collect()
        app = FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(320, 320))
        faces = app.get(img_ref)
        print("  => faces detected (retry):", len(faces))
    except Exception as e:
        print("Retry exception:", repr(e))
        faces = []

if not faces:
    try:
        print("Retry with buffalo_s model (smaller)...")
        del app
        gc.collect()
        app = FaceAnalysis(name="buffalo_s", providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(320, 320))
        faces = app.get(img_ref)
        print("  => faces detected (buffalo_s):", len(faces))
    except Exception as e:
        print("buffalo_s exception:", repr(e))
        faces = []

if not faces:
    print("\n❌ Không phát hiện mặt. Hãy thử các bước sau:")
    print("- Dùng ảnh frontal, mặt chiếm tỉ lệ lớn trong ảnh (crop lại nếu cần).")
    print("- Ảnh rõ nét, không che mặt, ánh sáng tốt.")
    raise SystemExit("No faces detected — provide a clearer frontal face image.")

# debug: draw boxes
img_boxes = img_ref.copy()
for i, f in enumerate(faces):
    bbox = np.asarray(f.bbox).astype(int)
    x1, y1, x2, y2 = bbox[:4]
    cv2.rectangle(img_boxes, (x1, y1), (x2, y2), (0, 255, 0), 2)
_debug_boxes = "/content/_debug_boxes.jpg"
cv2.imwrite(_debug_boxes, img_boxes)
try:
    _display(_IPImage(_debug_boxes))
except Exception:
    pass

# ----------------------------
# Extract FaceID embedding (ROBUST)
# ----------------------------
# build face embedding
faceid_np = faces[0].normed_embedding
faceid_embeds = torch.from_numpy(faceid_np).unsqueeze(0).to(device, dtype=dtype)
print("✅ FaceID embedding ready, shape:", faceid_embeds.shape)

# free app to save memory
try:
    del app
except:
    pass
gc.collect()
# ----------------------------
# Extract FaceID embedding (ROBUST)
# ----------------------------


# ----------------------------
# Load IP-Adapter-FaceID (check checkpoint)
# ----------------------------
if not os.path.exists(IP_CKPT):
    raise SystemExit(f"❌ Missing IP-Adapter checkpoint: {IP_CKPT} — download and place file there.")

print("🔹 Loading IP-Adapter-FaceID...")
ip_model = IPAdapterFaceIDXL(pipe, IP_CKPT, device)
print("✅ IP-Adapter-FaceIDXL loaded")

# ----------------------------
# Prompts
# ----------------------------
VEGALILI_PROMPT = (
    "VegaLili, 1girl, short hair, hair over one eye, ahoge, orange hair, pink eyes, "
    "pink bodysuit, purple jacket, hood down, headphones, ultra-detailed anime-style portrait, "
    "dynamic pose, cinematic lighting, photorealistic anime, highly detailed face and hair"
)

NEGATIVE_PROMPT = (
    "blurry, lowres, jpeg artifacts, extra fingers, bad hands, bad anatomy, "
    "childlike, cartoonish, unrealistic colors, watermark, text"
)

# ----------------------------
# Quick test (FaceID only)
# ----------------------------
# PROMPT = "portrait of a young woman, ultra-detailed, realistic lighting"
# NEG_PROMPT = "blurry, lowres, bad hands, cartoonish"

# print("🎨 Generating FaceID test...")
# # create generator compatibly
# if device == "cuda":
#     generator = torch.Generator(device=device).manual_seed(1234)
# else:
#     generator = torch.Generator().manual_seed(1234)

# canny_image = load_image(CANNY_PATH)

# result = ip_model.generate(
#     prompt=PROMPT,
#     negative_prompt=NEG_PROMPT,
#     num_inference_steps=20,
#     width=512,
#     height=512,
#     guidance_scale=7.0,
#     faceid_embeds=faceid_embeds,
#     control_image=canny_image,
#     seed=1234
# )

# img = result[0]
# img.save("faceid_test.png")
# print("✅ Saved faceid_test.png")
