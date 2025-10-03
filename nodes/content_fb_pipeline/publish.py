# nodes/content_and_facebook_node/node_publish.py
import traceback
import os
from services.facebook_service import FacebookPipeline

def post_media(pipeline: FacebookPipeline, video_path=None, image_path=None, fb_title="", fb_description=""):
    fb_title_safe = fb_title[:100]
    try:
        if video_path:
            fb_result = pipeline.post_video(
                video_path=video_path,
                title=fb_title_safe,
                description=fb_description
            )
            success = bool(fb_result.get("id"))
        elif image_path:
            fb_result = pipeline.run(
                image_path=image_path,
                title=fb_title,
                description=fb_description
            )
            success = bool(fb_result.get("published", False))
        else:
            success = False
    except Exception:
        traceback.print_exc()
        success = False
    return success

def cleanup_files(paths):
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            traceback.print_exc()
