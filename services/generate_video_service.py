# improved_quote_video.py
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
import math
import numpy as np
from moviepy import ImageSequenceClip
import textwrap
import os
import sys

# --------- Utils / Easing ----------
def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def smoothstep(t):
    return t * t * (3 - 2 * t)

def sinus_ease(t):
    return math.sin(t * math.pi / 2)

# safe font loader with fallback to a default PIL font
def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype("DejaVuSerif.ttf", size)
        except Exception:
            return ImageFont.load_default()

# wrap text to fit max_width using draw.textbbox measurement
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

# create subtle vignette mask
def vignette_mask(size, strength=0.6):
    w, h = size, size
    x = np.linspace(-1, 1, w)[None, :]
    y = np.linspace(-1, 1, h)[:, None]
    d = np.sqrt(x**2 + y**2)
    mask = 1 - np.clip((d - 0.5) / (1.0 - 0.5), 0, 1)
    mask = mask ** (1 + strength*2)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    return mask_img.filter(ImageFilter.GaussianBlur(radius=size*0.03))

# film grain overlay
def film_grain(size, amount=0.03):
    w, h = size, size
    noise = (np.random.randn(h, w) * 255 * amount + 127).clip(0,255).astype(np.uint8)
    return Image.fromarray(noise, mode="L").convert("RGBA").resize((w,h))

# rounded rectangle helper (approx)
def rounded_rect_mask(size, rect, radius):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    x0,y0,x1,y1 = rect
    draw.rounded_rectangle(rect, radius=radius, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(radius=radius*0.5))

# --------- Frame generator (improved visuals) ----------
def generate_frame(pil_image, text, author=None, size=512,
                   frame_index=0, total_frames=200,
                   scale_factor=1.35,
                   text_opacity=1.0,
                   font_quote_path="asset/fonts/NotoSerif-Medium.ttf",
                   font_author_path="asset/fonts/PlaywriteDESAS-Light.ttf",
                   motion_trail=0.12,   # blending with previous frame to simulate motion blur (0..0.5)
                   grain_amount=0.03,
                   bg_dof_max=1.8):
    progress = frame_index / max(1, total_frames - 1)
    # smoother timing
    t_smooth = ease_out_cubic(progress)
    t_sin = sinus_ease(progress)

    # --- background zoom/slow pan (parallax) ---
    zoom = scale_factor + 0.02 * math.sin(math.pi * progress * 2)  # tiny breathing
    tmp_w, tmp_h = int(size * zoom), int(size * zoom)
    tmp = pil_image.resize((tmp_w, tmp_h), Image.LANCZOS)

    # pan path: slow circular-ish motion
    pan_radius = (tmp_w - size) / 2
    pan_x = int((tmp_w - size)/2 + pan_radius * 0.18 * math.sin(2 * math.pi * progress))
    pan_y = int((tmp_h - size)/2 + pan_radius * 0.12 * math.cos(2 * math.pi * progress))
    base = tmp.crop((pan_x, pan_y, pan_x+size, pan_y+size)).convert("RGB")

    # small background depth-of-field effect (slightly blur edges depending on time)
    dof_amount = (0.5 + t_sin * 0.5) * bg_dof_max * 0.4
    base = base.filter(ImageFilter.GaussianBlur(radius=dof_amount))

    # color grade subtle
    base = ImageEnhance.Color(base).enhance(1.08)
    base = ImageEnhance.Brightness(base).enhance(1.02)
    base = ImageEnhance.Sharpness(base).enhance(0.95)

    # convert to RGBA for compositing
    frame = base.convert("RGBA")

    draw = ImageDraw.Draw(frame)
    padding = int(size * 0.12)
    max_width = size - 2*padding

    # fonts: size relative to image size
    quote_font_size = max(20, int(size * 0.072))
    author_font_size = max(14, int(size * 0.044))

    font_quote = load_font(font_quote_path, quote_font_size)
    font_author = load_font(font_author_path, author_font_size)

    # layout text lines
    tmp_draw = ImageDraw.Draw(frame)
    lines = wrap_text(tmp_draw, text, font_quote, max_width)

    # measure total text block height
    line_height = int(quote_font_size * 1.25)
    total_text_h = len(lines) * line_height

    # --- Create blurred plaque behind text for readability ---
    plaque_padding_x = int(padding * 0.6)
    plaque_padding_y = int(padding * 0.4)
    plaque_w = max_width + plaque_padding_x * 2
    plaque_h = total_text_h + plaque_padding_y * 2 + (author_font_size + 10 if author else 0)
    plaque_x = (size - plaque_w) // 2
    plaque_y = (size - plaque_h) // 2

    plaque_layer = Image.new("RGBA", (size, size), (0,0,0,0))
    # draw semi-transparent rounded rectangle then blur it for soft effect
    rr_mask = rounded_rect_mask(size, (plaque_x, plaque_y, plaque_x+plaque_w, plaque_y+plaque_h), radius=int(size*0.03))
    dark = Image.new("RGBA", (size, size), (10,10,10,int(110 * t_smooth * 0.9)))  # semi dark plaque
    plaque_layer = Image.composite(dark, plaque_layer, rr_mask)
    plaque_layer = plaque_layer.filter(ImageFilter.GaussianBlur(radius=size*0.008))
    frame = Image.alpha_composite(frame, plaque_layer)

    # --- Text drawing with subtle shadow and slide-in animation ---
    text_progress = smoothstep(min(1.0, progress * 2.2))  # text appears earlier than full length
    text_alpha = int(255 * text_opacity * text_progress)
    shadow_alpha = int(text_alpha * 0.25)

    x_center = size // 2
    y_start = plaque_y + plaque_padding_y + int((plaque_h - plaque_padding_y*2 - (author_font_size+10 if author else 0) - total_text_h) / 2)

    for i, line in enumerate(lines):
        # small per-line delay for staggered entrance
        line_t = min(1.0, max(0.0, (progress * 1.6) - i*0.03))
        line_e = ease_out_cubic(line_t)
        # measure
        w = draw.textbbox((0,0), line, font=font_quote)[2]
        x = x_center - w // 2
        # subtle vertical pop and horizontal slide
        y = int(y_start + i * line_height - (1 - line_e) * (size * 0.03))
        slide = int((1 - line_e) * size * 0.02)
        # shadow
        shadow = Image.new("RGBA", frame.size, (0,0,0,0))
        sd = ImageDraw.Draw(shadow)
        sd.text((x+slide+2, y+2), line, font=font_quote, fill=(0,0,0,shadow_alpha))
        frame = Image.alpha_composite(frame, shadow)
        # main text
        txt = Image.new("RGBA", frame.size, (0,0,0,0))
        td = ImageDraw.Draw(txt)
        td.text((x+slide, y), line, font=font_quote, fill=(255,255,255,text_alpha))
        frame = Image.alpha_composite(frame, txt)

    # author line
    if author:
        author_text = f"— {author}"
        w = draw.textbbox((0,0), author_text, font=font_author)[2]
        ay = plaque_y + plaque_h - plaque_padding_y - author_font_size
        # animate author fade-in slightly after text
        a_t = smoothstep(min(1.0, (progress - 0.18) * 2.5))
        a_alpha = int(220 * a_t)
        a_slide = int((1 - a_t) * size * 0.015)
        author_layer = Image.new("RGBA", frame.size, (0,0,0,0))
        ad = ImageDraw.Draw(author_layer)
        ad.text(((size - w)//2 + a_slide, ay), author_text, font=font_author, fill=(230,230,230,a_alpha))
        frame = Image.alpha_composite(frame, author_layer)

    # vignette
    vmask = vignette_mask(size, strength=0.7)
    vmask = ImageOps.invert(vmask)

    black = Image.new("RGBA", frame.size, (0, 0, 0, 120))  # alpha base (tweak 0..255)
    black.putalpha(vmask)
    frame = Image.alpha_composite(frame, black)

    # multiply vignette to darken edges: create black layer with vignette as alpha

    # film grain
    grain = film_grain(size, amount=grain_amount)
    grain.putalpha(int(40 * (0.9)))
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
    # load image
    pil = Image.open(img_path).convert("RGB")

    # center-crop or pad to square based on size to preserve aspect ratio of crop
    w0, h0 = pil.size
    # scale input so smaller side >= size

    width, height = size
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
        # motion trail: blend with previous to fake motion-blur (decay)
        if prev_frame is not None:
            trail_strength = 0.12  # adjust for blur amount; higher = more smear
            f = Image.blend(f, prev_frame, alpha=trail_strength)
        prev_frame = f.copy()
        frames.append(np.array(f.convert("RGB")))
        if (i+1) % 20 == 0 or i == total_frames - 1:
            print(f"  {i+1}/{total_frames} frames done")

    # build clip
    clip = ImageSequenceClip(frames, fps=fps)
    # write out with good encoding options
    clip.write_videofile(output, codec=codec, preset=preset, ffmpeg_params=["-crf", str(crf)])
    print(f"Đã xuất video: {output}")

# --------- CLI / Example usage ----------
if __name__ == "__main__":
    # Example: python improved_quote_video.py /path/to/img.jpg "Your quote here" "Author"
    if len(sys.argv) >= 3:
        img_path = sys.argv[1]
        quote = sys.argv[2]
        author = sys.argv[3] if len(sys.argv) >= 4 else None
    else:
        # fallback demo values (change to your real path)
        img_path = r"D:\duocnv\tytytu\generated_images\h1.jpg"
        quote = "The only true wisdom is in knowing you know nothing."
        author = "Socrates"

    generate_video(img_path, quote, author, output="quote_video_professional.mp4", size=720, total_frames=240, fps=30)
