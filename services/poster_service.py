from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageEnhance, ImageFilter
import requests
from io import BytesIO
import re

# ---------------- default font ----------------
DEFAULT_FONT_URL = "https://fonts.gstatic.com/s/notoserif/v33/ga6saw1J5X9T9RW6j9bNfFIMZhhWnFTyNZIQDzi_FXP0RgnaOg9MYBNLg8cPpKrCzyUi.ttf"

# ----------------------------------------------


# ----------------------------------------------

def load_font_from_url(url, size):
    resp = requests.get(url)
    resp.raise_for_status()
    return ImageFont.truetype(BytesIO(resp.content), size=size)

def choose_text_color_and_gradient(pil_image, tone="neutral", padding=60, gradient_alpha=90):
    """Chọn màu text + gradient, hiểu tone phức tạp như 'Warm, serene'."""
    width, height = pil_image.size
    central_area = pil_image.crop((padding, padding, width-padding, height-padding))
    stat = ImageStat.Stat(central_area)
    avg_r, avg_g, avg_b = stat.mean[:3]
    brightness = (avg_r + avg_g + avg_b)/3

    tone_map = {
        "happy":   ((255, 200, 100), (255, 120, 80)),
        "sad":     ((50, 80, 150),   (20, 40, 80)),
        "neutral": ((20, 120, 150),  (200, 60, 140)),
        "vibrant": ((255, 0, 100),   (255, 200, 0)),
        "warm":    ((255, 150, 80),  (200, 50, 50)),
        "cool":    ((80, 200, 255),  (0, 100, 200)),
        "pastel":  ((255, 180, 220), (180, 220, 255)),
        "bold":    ((20, 20, 20),    (200, 0, 0)),
        "calm":    ((120, 200, 180), (80, 150, 140)),
        "dark":    ((30, 30, 30),    (80, 0, 80)),
        "light":   ((240, 240, 240), (200, 220, 255)),
        "luxury":  ((30, 30, 30),    (200, 170, 0)),
        "natural": ((80, 150, 80),   (200, 180, 120)),
    }

    synonyms = {
        "serene": "calm",
        "peaceful": "calm",
        "tranquil": "calm",
        "joyful": "happy",
        "cheerful": "happy",
        "melancholy": "sad",
        "moody": "dark",
        "bright": "light",
    }

    parts = re.split(r"[,\;/\-\|]+|\band\b|\s+", tone.lower())
    tones = []
    for p in parts:
        if not p:
            continue
        if p in tone_map:
            tones.append(p)
        elif p in synonyms:
            tones.append(synonyms[p])

    if not tones:
        tones = ["neutral"]

    starts = [tone_map[t][0] for t in tones if t in tone_map]
    ends   = [tone_map[t][1] for t in tone_map]

    grad_start = tuple(sum(c[i] for c in starts)//len(starts) for i in range(3))
    grad_end   = tuple(sum(c[i] for c in ends)//len(ends) for i in range(3))

    text_color = (255, 255, 255) if brightness < 100 else (20, 20, 20)

    return text_color, grad_start, grad_end, gradient_alpha


def generate_poster(
    pil_image,
    text,
    author=None,
    tone="neutral",
    size=512,
    padding=60,
    font_size=48,
    line_spacing=10,
    brightness=0.6,
    saturation=1.4,
    gradient_alpha=10,
):
    """Trả về PIL.Image RGBA poster, text/gradient tự động đồng bộ tone/mood"""
    image = pil_image.resize((size, size)).convert("RGB")
    image = ImageEnhance.Color(image).enhance(saturation)
    image = ImageEnhance.Brightness(image).enhance(brightness)
    width, height = image.size

    # --- dùng font local ---
    font_quote = ImageFont.truetype("asset/fonts/NotoSerif-Medium.ttf", font_size)
    font_author = ImageFont.truetype("asset/fonts/PlaywriteDESAS-Light.ttf", int(font_size * 0.6))

    # thêm ❝ ❞ quanh text
    quote_text = f"“ {text.strip()} ”"

    # wrap text
    draw = ImageDraw.Draw(image)
    max_width = width - 2 * padding
    lines = []
    for paragraph in quote_text.split('\n'):
        words = paragraph.split(' ')
        line = ''
        for word in words:
            test_line = line + (' ' if line else '') + word
            bbox = draw.textbbox((0, 0), test_line, font=font_quote)
            if bbox[2] > max_width:
                if line:
                    lines.append(line)
                line = word
            else:
                line = test_line
        if line:
            lines.append(line)

    # chọn màu
    text_color, grad_start, grad_end, gradient_alpha = choose_text_color_and_gradient(
        image, tone=tone, padding=padding, gradient_alpha=gradient_alpha
    )

    # canh giữa theo chiều dọc
    ascent, descent = font_quote.getmetrics()
    line_height = ascent + descent
    total_height = line_height * len(lines) + line_spacing * (len(lines) - 1)
    y_start = padding + (height - 2 * padding - total_height) / 2

    # gradient overlay RGBA
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(gradient)
    for y in range(height):
        t = y / height
        r = int(grad_start[0] * (1-t) + grad_end[0]*t)
        g = int(grad_start[1] * (1-t) + grad_end[1]*t)
        b = int(grad_start[2] * (1-t) + grad_end[2]*t)
        gdraw.line([(0, y), (width, y)], fill=(r, g, b, gradient_alpha))

    image_rgba = Image.alpha_composite(image.convert("RGBA"), gradient)

    # vẽ text
    draw_rgba = ImageDraw.Draw(image_rgba)
    y_text = y_start
    for line in lines:
        bbox = draw_rgba.textbbox((0, 0), line, font=font_quote)
        w = bbox[2] - bbox[0]
        x_text = (width - w) / 2

        # --- tạo layer RGBA cho bóng ---
        shadow_layer = Image.new("RGBA", image_rgba.size, (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.text((x_text+2, y_text+2), line, font=font_quote, fill=(0,0,0,108))  # alpha 0-255

        # làm nhòe bóng
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(2))

        # hợp nhất bóng
        image_rgba = Image.alpha_composite(image_rgba, shadow_layer)

        # --- tạo layer RGBA cho chữ chính mờ ---
        txt_layer = Image.new("RGBA", image_rgba.size, (0,0,0,0))
        draw_layer = ImageDraw.Draw(txt_layer)
        draw_layer.text((x_text, y_text), line, font=font_quote, fill=(text_color[0], text_color[1], text_color[2], 220))

        # hợp nhất chữ
        image_rgba = Image.alpha_composite(image_rgba, txt_layer)

        y_text += line_height + line_spacing

    # sau vòng for line in lines
    draw_rgba = ImageDraw.Draw(image_rgba)  # tạo lại đối tượng Draw

    if author:
        author_text = f"— {author.strip('- ')}"
        bbox = draw_rgba.textbbox((0, 0), author_text, font=font_author)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x_text = (width - w) / 2

        bottom_offset = 40
        y_author = height - bottom_offset - h

        draw_rgba.text((x_text, y_author), author_text, font=font_author, 
                        fill=(text_color[0], text_color[1], text_color[2], 200))



    return image_rgba
