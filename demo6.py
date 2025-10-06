import asyncio
import os
import uuid
import requests
import textwrap
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
from PIL import Image, ImageDraw, ImageFont
from runware import Runware, IImageInference
from elevenlabs import ElevenLabs, save

# ---------------- Config ----------------
TEMP_DIR = "generated_reels"
os.makedirs(TEMP_DIR, exist_ok=True)

RUNWARE_API_KEY = "JDI7KlmsSb0j7wdPVKFS0X0B69EcpUoF"
ELEVEN_API_KEY = "sk_109a89e7b19bd2d1ee64d29accf88bb51dbae83dfeaa4a10"

# ---------------- Nội dung câu chuyện ----------------
story_texts = [
    {"speaker": "Nam", "text": "Uống gì?", "image_prompt": "A young man in a cafe asking a question"},
    {"speaker": "Nữ", "text": "Trà sữa trân châu.", "image_prompt": "A young woman smiling with bubble tea"},
    {"speaker": "Nam", "text": "Thôi anh uống theo em, miễn em trả tiền.", "image_prompt": "A playful man laughing"},
    {"speaker": "Nữ", "text": "Haha, lầy ghê.", "image_prompt": "A woman laughing playfully"}
]


# ---------------- Generate TTS ----------------
def generate_tts(text: str, speaker: str) -> str:
    client = ElevenLabs(api_key=ELEVEN_API_KEY)
    voice_id = "3VnrjnYrskPMDsapTr8X" if speaker == "Nam" else "X0V9HEDEuaVhVqzVPUKM"
    audio_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:4]}.mp3")
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_v3",
        output_format="mp3_44100_128"
    )
    save(audio, audio_path)
    return audio_path

# ---------------- Generate AI Image ----------------
async def generate_image(prompt: str) -> str:
    runware = Runware(api_key=RUNWARE_API_KEY)
    await runware.connect()
    request_image = IImageInference(
        positivePrompt=prompt,
        height=512,
        width=512,
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

# ---------------- Draw text on image ----------------
def draw_text_on_image(image_path: str, text: str, speaker: str) -> str:
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    font_path = "NotoSerif-Medium.ttf"
    font = ImageFont.truetype(font_path, size=40)
    color = "cyan" if speaker == "Nam" else "pink"

    wrapped_lines = []
    for line in text.split("\n"):
        wrapped_lines.extend(textwrap.wrap(line, width=25))

    line_heights = []
    max_line_w = 0
    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        line_heights.append(line_h)
        max_line_w = max(max_line_w, line_w)
    total_text_h = sum(line_heights) + (len(wrapped_lines)-1)*10

    w, h = img.size
    y = (h - total_text_h) / 2

    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        draw.text(((w - line_w)/2, y), line, font=font, fill=color)
        y += line_h + 10

    out_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:4]}_text.jpg")
    img.save(out_path)
    return out_path

# ---------------- Create video ----------------
def create_slideshow_video(image_paths: list, speaker_texts: list, audio_paths: list) -> str:
    slides = []
    audio_clips = []

    for i, img_path in enumerate(image_paths):
        img_with_text = draw_text_on_image(img_path, speaker_texts[i]['text'], speaker_texts[i]['speaker'])
        audio_clip = AudioFileClip(audio_paths[i])
        img_clip = ImageClip(img_with_text).set_duration(audio_clip.duration)
        slides.append(img_clip)
        audio_clips.append(audio_clip)

    video_clip = concatenate_videoclips(slides, method="compose")
    full_audio = concatenate_audioclips(audio_clips)
    video_clip = video_clip.set_audio(full_audio)

    output_video = os.path.join(TEMP_DIR, "trasua_reel.mp4")
    video_clip.write_videofile(output_video, fps=24)
    return output_video

# ---------------- Main ----------------
async def create_trasua_reel(story_texts):
    image_paths, audio_paths = [], []

    for s in story_texts:
        img_path = await generate_image(s['image_prompt'])
        audio_path = generate_tts(s['text'], s['speaker'])
        image_paths.append(img_path)
        audio_paths.append(audio_path)

    video_path = create_slideshow_video(image_paths, story_texts, audio_paths)
    return {"video_path": video_path}

# ---------------- Run ----------------
if __name__ == "__main__":
    result = asyncio.run(create_trasua_reel(story_texts))
    print("🎬 Video tạo xong:", result["video_path"])
