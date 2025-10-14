from PIL import Image as PILImage, ImageFilter
from IPython.display import display, Image
import torch

# ---------- config canvas ----------
OUT_W, OUT_H = 720, 1080  # phải chia hết cho 8

# ---------- load & resize init image (giữ tỉ lệ, căn giữa) ----------
bg = PILImage.open("v1real.png").convert("RGB")
# đảm bảo tỉ lệ và kích thước đúng với OUT_W x OUT_H
bg = bg.resize((OUT_W, OUT_H), PILImage.LANCZOS)

ZOOMED_INIT_PATH = "init_zoomed_out_resized.png"
bg.save(ZOOMED_INIT_PATH)
print("✅ Saved zoomed-out init image:", ZOOMED_INIT_PATH)

def to_image(result):
    return result[0] if isinstance(result, (list, tuple)) else result
# ---------- improved prompts (giữ nhận dạng) ----------

# PROMPT = (
#     "ultra realistic photo portrait of a real human woman, converted from anime, "
#     "high fidelity photorealistic skin, real human lighting and texture, cinematic tone, "
#     "soft lighting, realistic eyes and proportions, DSLR photograph, 8K, natural pose, "
#     "natural neck length, normal body proportions, realistic upper torso"
# )

# NEG_PROMPT = (
#     "cartoon, anime, painting, sketch, lowres, blurry, deformed body, bad hands, "
#     "revealing clothes, cleavage, short dress, unnatural lighting, extra limbs, watermark, text, logo, "
#     "distorted face, unrealistic proportions, oversmoothed skin, plastic skin, "
#     "elongated neck, long neck, stretched neck, thin stretched neck"
# )
# result = ip_model.generate(
#     prompt=PROMPT,
#     negative_prompt=NEG_PROMPT,
#     num_inference_steps=40,         # tăng từ 30 -> 40 (thử 50 nếu cần)
#     image=bg,
#     width=OUT_W,
#     height=OUT_H,
#     guidance_scale=8.5,             # giữ/gợi ý chi tiết
#     faceid_embeds=faceid_embeds_loaded_2,    # giữ embedding bạn có
#     faceid_guidance_scale=0.25,     # tăng lên (thử 0.15-0.6 để tìm sweet spot)
#     seed=5555544,
#     strength=0.45                   # giảm từ 0.6 -> ~0.4-0.5 để giữ hơn likeness
# )

# ---------- improved prompts (giữ nhận dạng) ----------
REALIFY_PROMPT = (
    "photo of a real human woman converted from anime, ultra realistic face, natural skin pores, "
    "true human eyes, natural lips, subtle imperfections, filmic color grading, "
    "soft light, realistic depth of field, no stylization, no anime"
)

REALIFY_NEG = (
    "anime, cartoon, cgi, painting, sketch, stylized, unrealistic skin, plastic, blurry, deformed, fake eyes"
)

stage1 = ip_model.generate(
    prompt=REALIFY_PROMPT,
    negative_prompt=REALIFY_NEG,
    image=bg,
    width=OUT_W,
    height=OUT_H,
    faceid_embeds=faceid_embeds_loaded_2,
    num_inference_steps=45,
    strength=0.65,           # Tăng lên để đẩy sang phong cách thật
    guidance_scale=9.5,      # mạnh hơn
    seed=123456,            # giảm từ 0.6 -> ~0.4-0.5 để giữ hơn likeness
)
stage1_img = to_image(stage1)
stage1_img.save("stage1_realify.png")
display(Image(filename="stage1_realify.png"))


REFINE_PROMPT = (
    "a cinematic photo portrait of a graceful, feminine woman walking forward and smiling softly, "
    "realistic lighting, 35mm film tone, natural bokeh, lifelike eyes, natural makeup, smooth motion, "
    "DSLR realism, masterpiece, cinematic photo"
)

REFINE_NEG = (
    "cartoon, anime, painting, cgi, plastic skin, overexposed, oversharpened, lowres, watermark, logo"
)

refined = ip_model.generate(
    prompt=REFINE_PROMPT,
    negative_prompt=REFINE_NEG,
    image=stage1_img,
    width=OUT_W,
    height=OUT_H,
    num_inference_steps=40,
    guidance_scale=8.5,
    faceid_embeds=faceid_embeds_loaded_2,
    faceid_guidance_scale=0.35,   # tăng nhẹ để giữ mặt
    strength=0.45,                # chỉ tinh chỉnh
    seed=888999,
)

final_img = to_image(refined)
final_img.save("stage2_refined_realistic.png")
display(Image(filename="stage2_refined_realistic.png"))
