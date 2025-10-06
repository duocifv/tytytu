import asyncio
import os
import uuid
import requests
from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import os, uuid
from runware import Runware, IImageInference
from pydantic import BaseModel
from elevenlabs import ElevenLabs, save

# ---------------- Cấu hình ----------------
TEMP_DIR = "generated_reels"
os.makedirs(TEMP_DIR, exist_ok=True)

RUNWARE_API_KEY = "JDI7KlmsSb0j7wdPVKFS0X0B69EcpUoF"
ELEVEN_API_KEY = "sk_109a89e7b19bd2d1ee64d29accf88bb51dbae83dfeaa4a10"

# ---------------- Schema Reels ----------------
class ReelsOutput(BaseModel):
    fb_title: str
    fb_description: str
    image_prompt: str

# ---------------- Hàm tạo nội dung ----------------
def create_content():
    return ReelsOutput(
        fb_title="Vượt Bão Giông: Sức Mạnh Đoàn Kết Của Việt Nam",
        fb_description="Dù thiên tai chồng chất, chúng ta không đơn độc. Nắm chặt tay nhau, cùng sẻ chia và kiến tạo lại.",
        image_prompt="Panoramic photo-editorial collage (3x3 with large center): center flooded Hanoi with families; surrounding panels clearly show medical aid (health), scattered money and falling stock overlay (finance), worried faces and phone alerts (psychology), idle factory and trucks (work), stormy sky with subtle geomagnetic bands (trend), family indoors caring for children and elderly (family), small meditation group (spiritual), volunteers distributing food (community). Modern, high-detail, cohesive, cinematic."
    )

# ---------------- Hàm tạo ảnh AI ----------------
async def generate_image(content_obj: ReelsOutput) -> str:
    runware = Runware(api_key=RUNWARE_API_KEY)
    await runware.connect()
    request_image = IImageInference(
        positivePrompt=content_obj.image_prompt,
        height=1024,
        width=1024,
        model="runware:100@1",
        steps=25,
        CFGScale=4.0,
        numberResults=1,
    )
    images = await runware.imageInference(requestImage=request_image)
    await runware.disconnect()

    img_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:4]}.jpg")
    img_data = requests.get(images[0].imageURL).content
    with open(img_path, "wb") as f:
        f.write(img_data)
    return img_path

# ---------------- Hàm tạo giọng đọc TTS ----------------
def generate_tts(content_obj: ReelsOutput) -> str:
    client = ElevenLabs(api_key=ELEVEN_API_KEY)
    audio_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:4]}.mp3")
    audio = client.text_to_speech.convert(
        text=content_obj.fb_title,
        voice_id="3VnrjnYrskPMDsapTr8X",
        model_id="eleven_v3",
        output_format="mp3_44100_128"
    )
    save(audio, audio_path)
    return audio_path

# ---------------- Hàm ghép video ----------------
def create_video(img_path: str, audio_path: str, text: str) -> str:
    image_clip = ImageClip(img_path).with_duration(10)
    audio_clip = AudioFileClip(audio_path)

    txt_clip = TextClip(
        font="NotoSerif-Medium.ttf",
        text=text,
        font_size=70,
        method="caption",
        size=(1024, 1024),
        color='white',
    ).with_duration(10).with_position('center')

    video_clip = CompositeVideoClip([image_clip, txt_clip]).with_audio(audio_clip)
    output_video = os.path.join(TEMP_DIR, f"reel_{uuid.uuid4().hex[:4]}.mp4")
    video_clip.write_videofile(output_video, fps=24)
    return output_video


def create_slideshow_video(image_paths: list, audio_path: str, texts: list, duration_per_slide=3) -> str:
    slides = []
    for i, img_path in enumerate(image_paths):
        # Image clip
        img_clip = ImageClip(img_path).with_duration(duration_per_slide)
        
        # Text clip
        text_clip = TextClip(
            font="NotoSerif-Medium.ttf",
            text=texts[i] if i < len(texts) else "",
            font_size=60,
            method="caption",
            size=(1024, 1024),
            color="white"
        ).with_duration(duration_per_slide).with_position("center")
        
        # Ghép text + hình
        slide = CompositeVideoClip([img_clip, text_clip])
        
        # Áp dụng fade bằng vfx
        slide = vfx.fadein(slide, 0.5)
        slide = vfx.fadeout(slide, 0.5)
        slides.append(slide)

    # Nối tất cả slide
    video_clip = concatenate_videoclips(slides, method="compose")
    
    # Thêm giọng đọc
    audio_clip = AudioFileClip(audio_path)
    audio_clip = audio_clip.with_duration(video_clip.duration)
    video_clip = video_clip.with_audio(audio_clip)
    
    # Xuất video
    output_video = os.path.join(TEMP_DIR, f"slideshow_{uuid.uuid4().hex[:4]}.mp4")
    video_clip.write_videofile(output_video, fps=24)
    
    return output_video

# ---------------- Hàm chính ----------------
async def node_reels_demo():
    content_obj = create_content()
    print("📌 Reels JSON:", content_obj)

    # Bạn có thể dùng ảnh + audio sẵn có để test, hoặc generate bằng API
    img_path = await generate_image(content_obj)
    audio_path = generate_tts(content_obj)

    output_video = create_video(img_path, audio_path, content_obj.fb_title)

    return {
        "status": "done",
        "content": content_obj,
        "image_path": img_path,
        "audio_path": audio_path,
        "video_path": output_video
    }

# ---------------- Ví dụ sử dụng ----------------
if __name__ == "__main__":
    import asyncio

    result = asyncio.run(node_reels_demo())
    print("🎬 Video tạo xong:", result["video_path"])

    
