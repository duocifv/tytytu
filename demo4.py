# modern_quote_video_smooth.py
"""
Phiên bản: mượt (smooth) cho video quote - giảm jitter/run-run.
Sử dụng: python modern_quote_video_smooth.py /path/to/img.jpg "Quote text" "Author"
"""
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
import math
import numpy as np
from moviepy import ImageSequenceClip
import os
import sys

# ---------------- Utils / Easing ----------------
def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def smoothstep(t):
    return t * t * (3 - 2 * t)

def sinus_ease(t):
    return math.sin(t * math.pi / 2)

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype("DejaVuSerif.ttf", size)
        except Exception:
            return ImageFont.load_default()

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

def vignette_mask(w, h, strength=0.6):
    x = np.linspace(-1,1,w)[None,:]
    y = np.linspace(-1,1,h)[:,None]
    d = np.sqrt(x**2 + y**2)
    mask = 1 - np.clip((d - 0.5) / (1-0.5), 0, 1)
    mask = mask ** (1 + strength*2)
    mask_img = Image.fromarray((mask*255).astype(np.uint8), mode="L")
    return mask_img.filter(ImageFilter.GaussianBlur(radius=max(w,h)*0.03))

def film_grain(w, h, amount=0.03):
    noise = (np.random.randn(h, w) * 255 * amount + 127).clip(0,255).astype(np.uint8)
    return Image.fromarray(noise, mode="L").convert("RGBA")

def rounded_rect_mask(w, h, rect, radius):
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(rect, radius=radius, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(radius=radius*0.5))

# ---------------- Frame Generator (renders at render_size then downscale) ----------------
def generate_frame(pil_image, text, author=None,
                   size=720,
                   render_size=None,   # if None => render_size = size (no oversample)
                   frame_index=0, total_frames=200,
                   scale_factor=1.25,
                   text_opacity=1.0,
                   font_quote_path=None,
                   font_author_path=None,
                   jitter_amp=0.003,   # fraction of size
                   pan_amp_x=0.06,     # fraction of pan radius
                   pan_amp_y=0.03,
                   grain_amount=0.025,
                   bg_dof_max=1.2):
    # decide render size
    if render_size is None:
        render_size = size
    R = int(render_size)
    progress = frame_index / max(1, total_frames - 1)
    t_smooth = ease_out_cubic(progress)
    t_sin = sinus_ease(progress)

    # --- Background zoom + smooth low-freq jitter + parallax ---
    zoom = scale_factor + 0.01 * math.sin(math.pi * progress * 2)  # tiny breathing
    tmp_w, tmp_h = int(R * zoom), int(R * zoom)
    tmp = pil_image.resize((tmp_w, tmp_h), Image.LANCZOS)

    # pan is low amplitude, low frequency for smoothness
    pan_radius = max(0, (tmp_w - R) / 2)
    pan_x_center = int((tmp_w - R) / 2)
    pan_y_center = int((tmp_h - R) / 2)
    pan_x = int(pan_x_center + pan_radius * pan_amp_x * math.sin(2 * math.pi * progress * 0.8))
    pan_y = int(pan_y_center + pan_radius * pan_amp_y * math.cos(2 * math.pi * progress * 0.6))

    # very subtle jitter at higher frequency but low amplitude
    jitter_x = int(math.sin(progress * 4.5 * math.pi) * R * jitter_amp)
    jitter_y = int(math.cos(progress * 3.7 * math.pi) * R * jitter_amp)

    crop_left = pan_x + jitter_x
    crop_top = pan_y + jitter_y
    base = tmp.crop((crop_left, crop_top, crop_left + R, crop_top + R)).convert("RGB")

    # small, smooth DoF
    dof_amount = (0.15 + t_sin * 0.45) * bg_dof_max * 0.6
    if dof_amount > 0.01:
        base = base.filter(ImageFilter.GaussianBlur(radius=dof_amount))

    # gentle color grade
    base = ImageEnhance.Color(base).enhance(1.08)
    base = ImageEnhance.Brightness(base).enhance(1.02)
    base = ImageEnhance.Sharpness(base).enhance(0.95)

    frame = base.convert("RGBA")
    draw = ImageDraw.Draw(frame)

    padding = int(R * 0.12)
    max_width = R - 2 * padding

    # fonts scale with render size
    # fonts scale với size cuối cùng, không bị downscale
    quote_font_size = max(24, int(size * 0.09))    # chữ quote lớn hơn
    author_font_size = max(14, int(size * 0.05))   # chữ author vừa
    font_quote = load_font(font_quote_path, quote_font_size) if font_quote_path else load_font(None, quote_font_size)
    font_author = load_font(font_author_path, author_font_size) if font_author_path else load_font(None, author_font_size)

    # text layout
    tmp_draw = ImageDraw.Draw(frame)
    lines = wrap_text(tmp_draw, text, font_quote, max_width)
    line_height = int(quote_font_size * 1.05)
    total_text_h = len(lines) * line_height

    # plaque
    plaque_padding_x = int(padding * 0.6)
    plaque_padding_y = int(padding * 0.4)
    plaque_w = max_width + plaque_padding_x * 2
    plaque_h = total_text_h + plaque_padding_y * 2 + (author_font_size + 10 if author else 0)
    plaque_x = (R - plaque_w) // 2
    plaque_y = (R - plaque_h) // 2

    plaque_layer = Image.new("RGBA", (R, R), (0, 0, 0, 0))
    rr_mask = rounded_rect_mask(R, R, (plaque_x, plaque_y, plaque_x + plaque_w, plaque_y + plaque_h), radius=int(R * 0.03))
    # plaque opacity grows with t_smooth (soft entry)
    dark_alpha = int(110 * t_smooth * 0.9)
    dark = Image.new("RGBA", (R, R), (8, 8, 8, dark_alpha))
    plaque_layer = Image.composite(dark, plaque_layer, rr_mask)
    plaque_layer = plaque_layer.filter(ImageFilter.GaussianBlur(radius=R * 0.007))
    frame = Image.alpha_composite(frame, plaque_layer)

    # text draw with stagger + pop + gentle glow
    text_progress = smoothstep(min(1.0, progress * 2.2))
    text_alpha = int(255 * text_opacity * text_progress)

    x_center = R // 2
    y_start = plaque_y + plaque_padding_y + int((plaque_h - plaque_padding_y * 2 - (author_font_size + 10 if author else 0) - total_text_h) / 2)

    for i, line in enumerate(lines):
        # stagger timing
        line_t = min(1.0, max(0.0, progress * 1.5 - i * 0.03))
        line_e = ease_out_cubic(line_t)
        w = draw.textbbox((0, 0), line, font=font_quote)[2]
        x = x_center - w // 2
        # pop + slide
        y = int(y_start + i * line_height - (1 - line_e) * (R * 0.025))
        slide = int((1 - line_e) * R * 0.015)

        # subtle glow: draw several blurred strokes with low alpha
        glow_color = (255, 100, 180)
        if line_e > 0.02:
            for radius in [5, 3]:
                glow = Image.new("RGBA", (R, R), (0, 0, 0, 0))
                gd = ImageDraw.Draw(glow)
                # stroke_fill for older pillow versions may be ignored; we simulate with multiple draws
                gd.text((x + slide, y), line, font=font_quote, fill=(*glow_color, int(40 * line_e)))
                glow = glow.filter(ImageFilter.GaussianBlur(radius=radius * (1.0 - line_e * 0.2)))
                frame = Image.alpha_composite(frame, glow)

        # main text
        txt = Image.new("RGBA", (R, R), (0, 0, 0, 0))
        td = ImageDraw.Draw(txt)
        td.text((x + slide, y), line, font=font_quote, fill=(255, 255, 255, text_alpha))
        frame = Image.alpha_composite(frame, txt)

    # author
    if author:
        author_text = f"— {author}"
        w = draw.textbbox((0, 0), author_text, font=font_author)[2]
        ay = plaque_y + plaque_h - plaque_padding_y - author_font_size
        a_t = smoothstep(min(1.0, (progress - 0.18) * 2.5))
        a_alpha = int(220 * a_t)
        a_slide = int((1 - a_t) * R * 0.01)
        author_layer = Image.new("RGBA", (R, R), (0, 0, 0, 0))
        ad = ImageDraw.Draw(author_layer)
        ad.text(((R - w) // 2 + a_slide, ay), author_text, font=font_author, fill=(230, 230, 230, a_alpha))
        frame = Image.alpha_composite(frame, author_layer)

    # vignette soft
    vmask = vignette_mask(R, R, strength=0.7)
    vmask = ImageOps.invert(vmask)
    black = Image.new("RGBA", (R, R), (0, 0, 0, 110))
    black.putalpha(vmask)
    frame = Image.alpha_composite(frame, black)

    # grain
    grain = film_grain(R, R, amount=grain_amount)
    grain.putalpha(int(36 * (0.9 + 0.1 * t_smooth)))
    frame = Image.alpha_composite(frame, grain)

    # downscale to final size if oversampled
    if R != size:
        frame = frame.resize((size, size), Image.LANCZOS)

    return frame

# ---------------- Video Generation (with multi-frame trail) ----------------
def generate_video(img_path, text, author=None,
                   output="quote_video_smooth.mp4",
                   size=720,
                   total_seconds=8,
                   fps=60,
                   codec="libx264",
                   preset="slow",
                   crf=18,
                   trail_frames=5,
                   oversample=1.4,
                   font_quote_path=None,
                   font_author_path=None):
    total_frames = int(total_seconds * fps)
    # load image
    pil = Image.open(img_path).convert("RGB")
    w0, h0 = pil.size
    # prepare oversampled pil for internal rendering
    render_size = int(size * oversample)
    # scale input so smaller side >= render_size
    scale = max(render_size / min(w0, h0), 1.0)
    target_w = int(w0 * scale)
    target_h = int(h0 * scale)
    pil = pil.resize((target_w, target_h), Image.LANCZOS)
    # center-crop square of side >= render_size
    left = (target_w - render_size) // 2
    top = (target_h - render_size) // 2
    pil = pil.crop((left, top, left + render_size, top + render_size))

    frames_rgb_arrays = []
    prev_pil_frames = []  # store PIL RGBA frames for trail blending

    print(f"Rendering {total_frames} frames @ {fps}fps (oversample={oversample})...")
    for i in range(total_frames):
        f_pil = generate_frame(pil, text, author,
                       size=size, render_size=render_size,
                       frame_index=i, total_frames=total_frames,
                       font_quote_path=font_quote_path, font_author_path=font_author_path,
                       jitter_amp=0.001, pan_amp_x=0.03, pan_amp_y=0.02,
                       grain_amount=0.020)
        # Motion trail: blend with several previous frames with decaying alpha and slight blur
        if prev_pil_frames:
            blended = f_pil.copy()
            # compute decay alphas (more recent frames stronger)
            # normalize so total added alpha reasonable
            decay = np.linspace(0.14, 0.03, min(trail_frames, len(prev_pil_frames)))
            for j, prev in enumerate(reversed(prev_pil_frames[-trail_frames:])):
                a = float(decay[j])
                # blur radius increases for older frames to simulate smear
                blur_r = 0.6 + j * 0.8
                prev_blur = prev.filter(ImageFilter.GaussianBlur(radius=blur_r))
                blended = Image.blend(blended, prev_blur, alpha=a)
            f_pil = blended

        # push current into prev buffer (keep only trail_frames recent)
        prev_pil_frames.append(f_pil.copy())
        if len(prev_pil_frames) > max(8, trail_frames * 2):
            prev_pil_frames.pop(0)

        # convert to RGB array for moviepy
        frames_rgb_arrays.append(np.array(f_pil.convert("RGB")))

        if (i + 1) % (max(1, total_frames // 8)) == 0 or i == total_frames - 1:
            print(f"  {i+1}/{total_frames} frames done")

    # build clip
    clip = ImageSequenceClip(frames_rgb_arrays, fps=fps)
    # set ffmpeg params
    ffmpeg_params = ["-crf", str(crf)]
    clip.write_videofile(output, codec=codec, preset=preset, ffmpeg_params=ffmpeg_params)
    print(f"Exported: {output}")

# ---------------- CLI / Example ----------------
if __name__ == "__main__":
    if len(sys.argv) >= 3:
        img_path = sys.argv[1]
        quote = sys.argv[2]
        author = sys.argv[3] if len(sys.argv) >= 4 else None
    else:
        img_path = r"D:\duocnv\tytytu\generated_images\h1.jpg"
        quote = "The only true wisdom is in knowing you know nothing."
        author = "Socrates"

    # bạn có thể chỉnh fps, total_seconds, trail_frames, oversample ở đây:
    generate_video(img_path, quote, author,
                   output="quote_video_smooth.mp4",
                   size=720,
                   total_seconds=8,
                   fps=60,
                   trail_frames=5,
                   oversample=1.4)
