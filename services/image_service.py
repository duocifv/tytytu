from dotenv import load_dotenv
load_dotenv()
import os
from huggingface_hub import InferenceClient
from PIL import Image

HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    raise RuntimeError("⚠️ Chưa set HF_TOKEN")

# Không dùng provider="nscale"
client = InferenceClient(api_key=HF_TOKEN)

def generate_image(prompt: str, out_file: str = "output.png"):
    image: Image.Image = client.text_to_image(
        prompt,
        model="stabilityai/stable-diffusion-xl-base-1.0",
    )
    image.save(out_file)
    print(f"✅ Ảnh đã lưu: {out_file}")
