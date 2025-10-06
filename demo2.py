import asyncio
import os
import uuid
from dotenv import load_dotenv
import requests
import textwrap
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from elevenlabs import ElevenLabs, save
import base64
from openai import OpenAI
import base64

# Load biến môi trường từ .env
load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))  # Set biến môi trường trước khi chạy


# ---------------- Config ----------------
TEMP_DIR = "generated_reels"
os.makedirs(TEMP_DIR, exist_ok=True)

STABILITY_API_KEY = "sk-NUW0FmCAiKTSTuqyUUQIbBT6UfK5dllhxMxMcdug2Q6FNr11"
ELEVEN_API_KEY = "sk_109a89e7b19bd2d1ee64d29accf88bb51dbae83dfeaa4a10"

# ---------------- Story JSON ----------------
story_texts = [
    {
        "scene": 1,
        "dialogue": {"male": "GPS này ghét người giàu à?", "female": "Ừ, nó đậu siêu xe mình trong sân khỉ kìa!"},
        "prompt": "A stunning young Korean couple, 20s, model/actor look, extremely stylish and sexy, man wearing women's blouse + men's trousers, woman wearing men's shirt + elegant skirt, faces and outfits consistent across all scenes. Scene 1: they stand shocked beside a luxury supercar stuck in a wild jungle, monkeys curiously surrounding them, expressions confused yet glamorous, cinematic lighting, vibrant colors, K-drama comedy style, contrast between wealth and wilderness."
    },
    {
        "scene": 2,
        "dialogue": {"male": "Bật lửa kim cương của anh sẽ cứu chúng ta!", "female": "Hay… nướng marshmallow trị giá cả tỷ đô?"},
        "prompt": "Same young Korean couple as scene 1, faces, body, and outfits consistent. Scene 2: man holding a diamond-studded lighter trying to start a fire, woman teasing with a tiny branch, exaggerated funny expressions. Background: dense jungle, cinematic lighting, bright colors, luxurious vs survival contrast, slapstick K-drama vibe."
    },
    {
        "scene": 3,
        "dialogue": {"male": "Anh mệt… nhưng vẫn đẹp trai chứ?", "female": "Đương nhiên! Mai mình xây biệt thự trên cây, thuê khỉ làm nhân viên!"},
        "prompt": "Same young Korean couple as previous scenes, faces and outfits consistent. Scene 3: sitting exhausted on a log, surrounded by luxury handbags, sparkling jewelry, and playful monkeys, funny expressions, cinematic lighting, vibrant colors, luxury parody style, humorous and whimsical mood."
    }
]

# ---------------- Generate TTS ----------------
def generate_tts(text: str, speaker: str) -> str:
    client = ElevenLabs(api_key=ELEVEN_API_KEY)
    voice_id = "3VnrjnYrskPMDsapTr8X" if speaker == "male" else "X0V9HEDEuaVhVqzVPUKM"
    audio_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:4]}_{speaker}.mp3")
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_v3",
        output_format="mp3_44100_128"
    )
    save(audio, audio_path)
    return audio_path

# ---------------- Generate AI Image with OpenAI ----------------
async def generate_image(prompt: str, scene_num: int = 0) -> str:
    """
    Tải ảnh placeholder từ Lorem Picsum để test video
    """
    # Tạo URL ảnh ngẫu nhiên
    width, height = 1024, 1024
    url = f"https://picsum.photos/{width}/{height}?random={uuid.uuid4().hex[:6]}"

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Cannot download image from {url}")

    img_path = os.path.join(TEMP_DIR, f"lorem_{uuid.uuid4().hex[:4]}.jpg")
    with open(img_path, "wb") as f:
        f.write(response.content)

    return img_path

# ---------------- Draw single dialogue on image ----------------
def draw_text_on_image(image_path: str, speaker: str, text: str) -> str:
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    font_path = "NotoSerif-Medium.ttf"
    font = ImageFont.truetype(font_path, size=50)

    wrapped_lines = textwrap.wrap(text, width=25)
    w, h = img.size
    total_text_h = sum([draw.textbbox((0,0), line, font=font)[3]-draw.textbbox((0,0), line, font=font)[1] for line in wrapped_lines]) + (len(wrapped_lines)-1)*10
    y = (h - total_text_h)/2
    color = "cyan" if speaker=="male" else "pink"

    for line in wrapped_lines:
        bbox = draw.textbbox((0,0), line, font=font)
        line_w = bbox[2]-bbox[0]
        line_h = bbox[3]-bbox[1]
        draw.text(((w-line_w)/2, y), line, font=font, fill=color)
        y += line_h + 10

    out_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:4]}_{speaker}_text.png")
    img.save(out_path)
    return out_path

# ---------------- Create video ----------------
def create_slideshow_video(image_paths: list, audio_paths: list) -> str:
    clips = []
    for img_path, audio_path in zip(image_paths, audio_paths):
        audio_clip = AudioFileClip(audio_path)
        img_clip = ImageClip(img_path).set_duration(audio_clip.duration)
        img_clip = img_clip.set_audio(audio_clip)
        clips.append(img_clip)

    final_video = concatenate_videoclips(clips, method="compose")
    output_video = os.path.join(TEMP_DIR, "trasua_reel.mp4")
    final_video.write_videofile(output_video, fps=24)
    return output_video

# ---------------- Main ----------------
async def create_trasua_reel(story_texts):
    image_paths, audio_paths = [], []

    for s in story_texts:
        img_path = await generate_image(s['prompt'])

        # Tạo clip nam
        img_male = draw_text_on_image(img_path, "male", s['dialogue']['male'])
        audio_male = generate_tts(s['dialogue']['male'], "male")
        image_paths.append(img_male)
        audio_paths.append(audio_male)

        # Tạo clip nữ
        img_female = draw_text_on_image(img_path, "female", s['dialogue']['female'])
        audio_female = generate_tts(s['dialogue']['female'], "female")
        image_paths.append(img_female)
        audio_paths.append(audio_female)

    video_path = create_slideshow_video(image_paths, audio_paths)
    return {"video_path": video_path}

# ---------------- Run ----------------
if __name__ == "__main__":
    result = asyncio.run(create_trasua_reel(story_texts))
    print("🎬 Video tạo xong:", result["video_path"])
