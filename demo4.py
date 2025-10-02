

# --------- CLI ----------
import sys
from services.generate_video_service import generate_video


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        img_path = sys.argv[1]
        quote = sys.argv[2]
        author = sys.argv[3] if len(sys.argv) >= 4 else None
    else:
        img_path = r"D:\duocnv\tytytu\generated_images\h1.jpg"
        quote = "The only true wisdom is in knowing you know nothing."
        author = "Socrates"

    generate_video(img_path, quote, author, output="quote_video_professional.mp4", size=(1080,1350), total_frames=180, fps=30)
