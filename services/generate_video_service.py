# improved_quote_video.py
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
import math
import numpy as np
from moviepy import ImageSequenceClip
import os
import sys

# --------- Utils / Easing ----------
def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def smoothstep(t):
    return t * t * (3 - 2 * t)

def sinus_ease(t):
    return math.sin(t * math.pi / 2)

# safe font loader with fallback
def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype("DejaVuSerif.ttf", size)
        except Exception:
            return ImageFont.load_default()

# wrap text to fit max_width
def wrap_text(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split(" ")
        line = words[0]
        for w in words[1:]:
            test = f"{line} {w}"
            if draw.textbbox((0,0), test, font=font)[2] <= max_width:
                line = test
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)
    return lines

# subtle vignette
def vignette_mask(size, strength=0.6, center_radius=0.77):
    width, height = size if isinstance(size, tuple) else (size, size)
    x = np.linspace(-1, 1, width)[None, :]
    y = np.linspace(-1, 1, height)[:, None]
    d = np.sqrt(x**2 + y**2)
    mask = 1 - np.clip((d - center_radius) / (1.0 - center_radius), 0, 1)
    mask = mask ** (1 + strength*2)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    return mask_img.filter(ImageFilter.GaussianBlur(radius=min(width,height)*0.03))

# film grain overlay
def film_grain(size, amount=0.03):
    width, height = size if isinstance(size, tuple) else (size, size)
    noise = (np.random.randn(height, width) * 255 * amount + 127).clip(0,255).astype(np.uint8)
    return Image.fromarray(noise, mode="L").convert("RGBA").resize((width,height))

# rounded rectangle mask
def rounded_rect_mask(size, rect, radius):
    width, height = size if isinstance(size, tuple) else (size, size)
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(rect, radius=radius, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(radius=radius*0.5))

# --------- Frame generator ----------
def generate_frame(pil_image, text, author=None, size=512,
                   frame_index=0, total_frames=200,
                   scale_factor=1.35,
                   text_opacity=1.0,
                   font_quote_path="asset/fonts/NotoSerif-Medium.ttf",
                   font_author_path="asset/fonts/PlaywriteDESAS-Light.ttf",
                   motion_trail=0.12,
                   grain_amount=0.03,
                   bg_dof_max=1.8):

    width, height = size if isinstance(size, tuple) else (size, size)
    progress = frame_index / max(1, total_frames - 1)
    t_smooth = ease_out_cubic(progress)
    t_sin = sinus_ease(progress)

    # --- background zoom/pan ---
    zoom = scale_factor + 0.02 * math.sin(math.pi * progress * 2)
    tmp_w, tmp_h = int(width * zoom), int(height * zoom)
    tmp = pil_image.resize((tmp_w, tmp_h), Image.LANCZOS)

    pan_radius = (tmp_w - width) / 2
    pan_x = int((tmp_w - width)/2 + pan_radius * 0.18 * math.sin(2 * math.pi * progress))
    pan_y = int((tmp_h - height)/2 + pan_radius * 0.12 * math.cos(2 * math.pi * progress))
    base = tmp.crop((pan_x, pan_y, pan_x+width, pan_y+height)).convert("RGB")

    # subtle depth-of-field
    dof_amount = (0.5 + t_sin * 0.5) * bg_dof_max * 0.4
    base = base.filter(ImageFilter.GaussianBlur(radius=dof_amount))

    # color grade
    base = ImageEnhance.Color(base).enhance(1.08)
    base = ImageEnhance.Brightness(base).enhance(1.02)
    base = ImageEnhance.Sharpness(base).enhance(0.95)

    frame = base.convert("RGBA")

    draw = ImageDraw.Draw(frame)
    padding = int(width * 0.12)
    max_width = width - 2*padding

    quote_font_size = max(20, int(width * 0.072))
    author_font_size = max(14, int(width * 0.044))

    font_quote = load_font(font_quote_path, quote_font_size)
    font_author = load_font(font_author_path, author_font_size)

    tmp_draw = ImageDraw.Draw(frame)
    lines = wrap_text(tmp_draw, text, font_quote, max_width)

    line_height = int(quote_font_size * 1.25)
    total_text_h = len(lines) * line_height

    # plaque behind text
    plaque_padding_x = int(padding * 0.6)
    plaque_padding_y = int(padding * 0.4)
    plaque_w = max_width + plaque_padding_x * 2
    plaque_h = total_text_h + plaque_padding_y * 2 + (author_font_size + 10 if author else 0)
    plaque_x = (width - plaque_w) // 2
    plaque_y = (height - plaque_h) // 2

    # --- tạo plaque oval đứng ---
    plaque_layer = Image.new("RGBA", (width, height), (0,0,0,0))
    oval_mask = Image.new("L", (width, height), 0)
    od = ImageDraw.Draw(oval_mask)
    # tạo oval đứng, rộng = plaque_w, cao = plaque_h
    od.ellipse((plaque_x, plaque_y, plaque_x+plaque_w, plaque_y+plaque_h), fill=255)
    # làm mềm viền bằng blur
    oval_mask = oval_mask.filter(ImageFilter.GaussianBlur(radius=width*0.015))

    # layer màu tối, alpha vừa phải để mờ
    dark = Image.new("RGBA", (width, height), (10,10,10,int(40 * t_smooth)))  # giảm alpha để mờ
    plaque_layer = Image.composite(dark, plaque_layer, oval_mask)

    # ghép vào frame
    frame = Image.alpha_composite(frame, plaque_layer)




    # text with shadow
    text_progress = smoothstep(min(1.0, progress * 2.2))
    text_alpha = int(255 * text_opacity * text_progress)
    shadow_alpha = int(text_alpha * 0.25)

    x_center = width // 2
    y_start = plaque_y + plaque_padding_y + int((plaque_h - plaque_padding_y*2 - (author_font_size+10 if author else 0) - total_text_h) / 2)

    for i, line in enumerate(lines):
        line_t = min(1.0, max(0.0, (progress * 2.5) - i*0.01))
        line_e = ease_out_cubic(line_t)
        w = draw.textbbox((0,0), line, font=font_quote)[2]
        x = x_center - w // 2
        y = int(y_start + i * line_height - (1 - line_e) * (height * 0.03))
        slide = int((1 - line_e) * width * 0.02)

        shadow = Image.new("RGBA", frame.size, (0,0,0,0))
        sd = ImageDraw.Draw(shadow)
        sd.text((x+slide+2, y+2), line, font=font_quote, fill=(0,0,0,shadow_alpha))
        frame = Image.alpha_composite(frame, shadow)

        txt = Image.new("RGBA", frame.size, (0,0,0,0))
        td = ImageDraw.Draw(txt)
        td.text((x+slide, y), line, font=font_quote, fill=(255,255,255,text_alpha))
        frame = Image.alpha_composite(frame, txt)

    # author
    if author:
        author_text = f"— {author}"
        w = draw.textbbox((0,0), author_text, font=font_author)[2]
        ay = plaque_y + plaque_h - plaque_padding_y - author_font_size
        a_t = smoothstep(min(1.0, (progress - 0.1) * 3.0))
        a_alpha = int(220 * a_t)
        a_slide = int((1 - a_t) * width * 0.015)
        author_layer = Image.new("RGBA", frame.size, (0,0,0,0))
        ad = ImageDraw.Draw(author_layer)
        ad.text(((width - w)//2 + a_slide, ay), author_text, font=font_author, fill=(230,230,230,a_alpha))
        frame = Image.alpha_composite(frame, author_layer)

    # Lấy màu trung bình nền video
    def average_color(img):
        # resize nhỏ để tính nhanh
        small = img.resize((16,16))
        arr = np.array(small)
        avg = arr.mean(axis=(0,1))
        return tuple(int(c) for c in avg)

    # --------- trong generate_frame, thay cho vignette cũ ---------
    vmask = vignette_mask(size, strength=0.7)
    vmask = ImageOps.invert(vmask)
    
    alpha_scale = 0.8  # 0.0 = trong suốt hoàn toàn, 1.0 = full
    # scale mask để giảm bóng
    vmask = vmask.point(lambda p: int(p * alpha_scale))

    avg_color = average_color(base)  # lấy màu từ background đã blur/color grade
    color_layer = Image.new("RGBA", frame.size, avg_color + (180,))  # thêm alpha
    color_layer.putalpha(vmask)
    frame = Image.alpha_composite(frame, color_layer)

    # film grain
    grain = film_grain(size, amount=grain_amount)
    grain.putalpha(int(38 * 0.9))
    frame = Image.alpha_composite(frame, grain)

    return frame

# --------- Video generation ----------
def generate_video(img_path, text, author=None,
                   output="quote_video_professional.mp4",
                   size=720,
                   total_frames=240,
                   fps=30,
                   codec="libx264",
                   preset="slow",
                   crf=18,
                   temp_preview=False):

    pil = Image.open(img_path).convert("RGB")
    if isinstance(size, int):
        size = (size, size)
    width, height = size
    w0, h0 = pil.size
    scale = max(width / w0, height / h0)
    target_w = int(w0 * scale)
    target_h = int(h0 * scale)
    pil = pil.resize((target_w, target_h), Image.LANCZOS)
    left = (target_w - width) // 2
    top = (target_h - height) // 2
    pil = pil.crop((left, top, left + width, top + height))

    frames = []
    prev_frame = None
    print("Generating frames:")
    for i in range(total_frames):
        f = generate_frame(pil, text, author, size=size, frame_index=i, total_frames=total_frames)
        if prev_frame is not None:
            f = Image.blend(f, prev_frame, alpha=0.12)
        prev_frame = f.copy()
        frames.append(np.array(f.convert("RGB")))
        if (i+1) % 20 == 0 or i == total_frames-1:
            print(f"  {i+1}/{total_frames} frames done")

    clip = ImageSequenceClip(frames, fps=fps)
    clip.write_videofile(output, codec=codec, preset=preset, ffmpeg_params=["-crf", str(crf)])
    print(f"Đã xuất video: {output}")

# --------- CLI ----------
if __name__ == "__main__":
    if len(sys.argv) >= 3:
        img_path = sys.argv[1]
        quote = sys.argv[2]
        author = sys.argv[3] if len(sys.argv) >= 4 else None
    else:
        img_path = r"D:\duocnv\tytytu\generated_images\h1.jpg"
        quote = "The only true wisdom is in knowing you know nothing."
        author = "Socrates"

    generate_video(img_path, quote, author, output="quote_video_professional.mp4", size=720, total_frames=240, fps=30)
