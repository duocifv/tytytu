import asyncio
import os
import uuid
from dotenv import load_dotenv
import textwrap
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from elevenlabs import ElevenLabs, save
import asyncio
from services.modelslab_service import generate_image_direct


# Load biến môi trường từ .env
load_dotenv()

# ---------------- Config ----------------
TEMP_DIR = "generated_reels"
os.makedirs(TEMP_DIR, exist_ok=True)

STABILITY_API_KEY = "sk-NUW0FmCAiKTSTuqyUUQIbBT6UfK5dllhxMxMcdug2Q6FNr11"
ELEVEN_API_KEY = "sk_109a89e7b19bd2d1ee64d29accf88bb51dbae83dfeaa4a10"

# ---------------- Story JSON ----------------
story_texts = [
    {
        "scene": 1,
        "dialogue": {
            "male": "Cầm giúp anh mảnh giấy này nhé… chỉ là vài dòng, nhưng có lẽ đủ để em hiểu anh.",
            "female": "Thư tình à? Anh vẫn còn tin vào những thứ đó sao?"
        },
        "prompt": "Consistent characters: female like Boa Hancock (shoulder-length hair, beige sweater, small necklace) & male like Zoro (short black hair, navy jacket, white shirt); keep same face/hair/outfit/accessories across all scenes (same seed/reference) — Bus stop at dusk: Minh kneels and places a folded note near Linh’s hand, cool sunset light, 3:2, 35mm film, shallow DOF, cinematic color grading."
    },
    {
        "scene": 2,
        "dialogue": {
            "male": "Anh biết mình đã sai… và sẽ thay đổi, dù chỉ từng chút một.",
            "female": "Từng chút một… liệu có đủ không, anh?"
        },
        "prompt": "Consistent characters: female like Boa Hancock & male like Zoro; keep same face/hair/outfit/accessories (same seed/reference) — Train station at daytime: Linh sits reading the folded note, Minh stands nearby waiting, cool light, close-up shot, 3:2, 35mm film, shallow DOF, cinematic color grading."
    },
    {
        "scene": 3,
        "dialogue": {
            "male": "Anh đã viết ra mọi điều anh sẽ làm… em nói đi, anh nên bắt đầu từ đâu?",
            "female": "Bắt đầu bằng việc đừng biến những lỗi nhỏ thành lý do để rời xa nhau."
        },
        "prompt": "Consistent characters: female like Boa Hancock & male like Zoro; keep full appearance (same seed/reference) — Café scene: both sit facing each other, folded note on the table between them, neutral warm light, medium-close shot, 3:2, 35mm film, shallow DOF, cinematic color grading."
    },
    {
        "scene": 4,
        "dialogue": {
            "male": "Anh đã làm như những gì đã hứa… em xem đi.",
            "female": "Em thấy rồi. Anh đã làm thật — không chỉ nói suông."
        },
        "prompt": "Consistent characters: female like Boa Hancock & male like Zoro; keep same outfit and appearance (same seed/reference) — Action close-up: Minh’s hand unfolds the note with the words 'already done', soft golden light, 3:2, 35mm film, shallow DOF, cinematic color grading."
    },
    {
        "scene": 5,
        "dialogue": {
            "male": "Cảm ơn em vì đã cho anh thời gian… anh sẽ không để nó trôi qua vô nghĩa.",
            "female": "Cho nhau một cơ hội không dễ, nhưng… mình thử lại nhé, từ hôm nay."
        },
        "prompt": "Consistent characters: female like Boa Hancock & male like Zoro; keep same face/hair/outfit/accessories (same seed/reference) — Balcony at sunrise: Linh hands Minh the folded note with a torn edge, soft golden morning light, wide-to-close framing, 3:2, 35mm film, shallow DOF, cinematic color grading."
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
    Chạy hàm blocking generate_image_from_prompt trong thread và await kết quả.
    Trả về đường dẫn file ảnh khi thành công, raise nếu thất bại.
    """
    output_base = f"scene_{scene_num}"
    print(f"🔁 [scene {scene_num}] Requesting image generation...")

    # chạy hàm blocking trong thread để không block event loop
    output_file = await asyncio.to_thread(generate_image_direct, prompt, output_base)

    if not output_file:
        # in debug file(s) nếu có
        print(f"❌ [scene {scene_num}] generate_image_from_prompt returned None. Kiểm tra debug_fetch_*.json")
        raise RuntimeError(f"❌ Tạo ảnh thất bại cho scene {scene_num}")

    print(f"✅ [scene {scene_num}] Image generated -> {output_file}")
    return output_file

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

    for idx, s in enumerate(story_texts):
        img_path = await generate_image(s['prompt'], scene_num=idx)

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
