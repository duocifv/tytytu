from fastapi import FastAPI
from pydantic import BaseModel
from diffusers import StableDiffusionPipeline, LMSDiscreteScheduler
import torch
import os
import uuid
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv() # Load Cloudinary config từ .env

app = FastAPI()

# Cấu hình Cloudinary

cloudinary.config(
cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
api_key=os.getenv("CLOUDINARY_API_KEY"),
api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

TEMP_DIR = "generated_images"
os.makedirs(TEMP_DIR, exist_ok=True)

# Load model với LMS scheduler

model_id = "sd-legacy/stable-diffusion-v1-5"
pipe = StableDiffusionPipeline.from_pretrained(
model_id,
torch_dtype=torch.float32
)
pipe.scheduler = LMSDiscreteScheduler.from_config(pipe.scheduler.config)
pipe.to("cpu")

class ImageRequest(BaseModel):
prompt: str

@app.post("/generate-image")
def generate_image(request: ImageRequest):
try: # Tạo ảnh
image = pipe(request.prompt).images[0]

        # Lưu tạm
        local_filename = os.path.join(TEMP_DIR, f"generated_image_{uuid.uuid4().hex}.png")
        image.save(local_filename)

        # Upload lên Cloudinary
        upload_result = cloudinary.uploader.upload(local_filename)
        image_url = upload_result.get("secure_url")

        # Xóa file tạm
        os.remove(local_filename)

        return {"image_url": image_url}

    except Exception as e:
        return {"error": f"Image generation failed: {e}"}
