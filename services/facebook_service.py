# services/facebook_service.py
import requests
import os
from dotenv import load_dotenv
import math
import time

# Load biến môi trường từ .env
load_dotenv()

class FacebookPipeline:
    """
    Service tương tác với Facebook Page:
      - Đăng bài text/link
      - Đăng ảnh (photos)
      - Đăng video (videos) -> hỗ trợ direct upload (nhỏ) và resumable upload (lớn)
      - Lấy info page
    """

    def __init__(self):
        self.page_id = os.getenv("FB_PAGE_ID")
        self.access_token = os.getenv("FB_PAGE_ACCESS_TOKEN")

        if not self.page_id or not self.access_token:
            raise ValueError("❌ FB_PAGE_ID hoặc FB_PAGE_ACCESS_TOKEN chưa được cấu hình!")

        # base URL for Graph API (page-scoped)
        self.base_url = f"https://graph.facebook.com/v23.0/{self.page_id}"

        # chunk size for resumable uploads (8 MB default)
        self.chunk_size = int(os.getenv("FB_VIDEO_CHUNK_SIZE", 8 * 1024 * 1024))

    # ---------------------------
    # Helper low-level requests
    # ---------------------------
    def _post(self, url, data=None, params=None, files=None, timeout=120):
        try:
            res = requests.post(url, data=data, params=params, files=files, timeout=timeout)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            # try to include response text if present
            text = getattr(e.response, "text", None) if hasattr(e, "response") else None
            return {"error": str(e), "response": text}

    def _get(self, url, params=None, timeout=30):
        try:
            res = requests.get(url, params=params, timeout=timeout)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            text = getattr(e.response, "text", None) if hasattr(e, "response") else None
            return {"error": str(e), "response": text}

    # ---------------------------
    # Post message
    # ---------------------------
    def post_message(self, message: str, link: str = None) -> dict:
        """Đăng bài lên Page. Nếu muốn gắn link thì truyền `link`."""
        data = {"message": message, "access_token": self.access_token}
        if link:
            data["link"] = link

        url = f"{self.base_url}/feed"
        return self._post(url, data=data)

    # ---------------------------
    # Post photo
    # ---------------------------
    def post_photo(self, image_path: str, caption: str = "") -> dict:
        """Đăng ảnh lên Page kèm caption"""
        url = f"{self.base_url}/photos"
        files = None
        fobj = None
        try:
            fobj = open(image_path, "rb")
            files = {"source": fobj}
            data = {"caption": caption, "access_token": self.access_token}
            return self._post(url, data=data, files=files)
        except Exception as e:
            return {"error": str(e)}
        finally:
            if fobj:
                try:
                    fobj.close()
                except Exception:
                    pass

    # ---------------------------
    # Post video (simple direct upload - small files)
    # ---------------------------
    def post_video_direct(self, video_path: str, title: str = "", description: str = "") -> dict:
        """
        Direct upload video using /{page_id}/videos with 'source' file.
        Works for small videos (often < ~50-100MB depending on network).
        """
        url = f"{self.base_url}/videos"
        fobj = None
        try:
            fobj = open(video_path, "rb")
            files = {"source": fobj}
            data = {
                "title": title,
                "description": description,
                "access_token": self.access_token
            }
            # Use a longer timeout for upload
            res = requests.post(url, files=files, data=data, timeout=600)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            text = getattr(e.response, "text", None) if hasattr(e, "response") else None
            return {"error": str(e), "response": text}
        except Exception as e:
            return {"error": str(e)}
        finally:
            if fobj:
                try:
                    fobj.close()
                except Exception:
                    pass

    # ---------------------------
    # Resumable upload for large videos
    # ---------------------------
    def post_video_resumable(self, video_path: str, title: str = "", description: str = "") -> dict:
        """
        Use Graph API resumable upload for large video files.
        Steps:
         1) POST /{page_id}/videos?upload_phase=start&file_size={size}
         2) POST /{page_id}/videos?upload_phase=transfer with 'video_file_chunk' (repeat until done)
         3) POST /{page_id}/videos?upload_phase=finish&upload_session_id={id}
        """
        file_size = os.path.getsize(video_path)
        url = f"{self.base_url}/videos"
        params_start = {
            "upload_phase": "start",
            "file_size": str(file_size),
            "access_token": self.access_token
        }
        try:
            # 1) start
            res_start = requests.post(url, params=params_start, timeout=30)
            res_start.raise_for_status()
            start_data = res_start.json()
            upload_session_id = start_data.get("upload_session_id") or start_data.get("upload_session")
            video_id = start_data.get("video_id")  # sometimes returned
            start_offset = int(start_data.get("start_offset", 0))
            end_offset = int(start_data.get("end_offset", 0))

            if not upload_session_id:
                return {"error": "No upload_session_id returned", "response": start_data}

            # 2) transfer in chunks
            with open(video_path, "rb") as f:
                offset = start_offset
                # Seek to start_offset
                f.seek(offset)
                chunk_i = 0
                while offset < file_size:
                    chunk_data = f.read(self.chunk_size)
                    if not chunk_data:
                        break
                    files = {
                        "video_file_chunk": ("chunk", chunk_data, "application/octet-stream")
                    }
                    params_transfer = {
                        "upload_phase": "transfer",
                        "upload_session_id": upload_session_id,
                        "start_offset": str(offset),
                        "access_token": self.access_token
                    }
                    # send chunk (long timeout)
                    res_transfer = requests.post(url, params=params_transfer, files=files, timeout=120)
                    try:
                        res_transfer.raise_for_status()
                    except requests.RequestException as e:
                        text = getattr(e.response, "text", None) if hasattr(e, "response") else None
                        return {"error": f"Chunk upload failed at offset {offset}: {e}", "response": text}
                    transfer_data = res_transfer.json()
                    # next offset
                    try:
                        offset = int(transfer_data.get("start_offset", offset))
                        # server may return next start_offset or end_offset; some sessions return 'start_offset' updated
                        if "start_offset" in transfer_data and int(transfer_data.get("start_offset")) > offset:
                            offset = int(transfer_data.get("start_offset"))
                        if "end_offset" in transfer_data:
                            offset = int(transfer_data.get("end_offset"))
                    except Exception:
                        # fallback increment by chunk size if server not informative
                        offset += len(chunk_data)
                    chunk_i += 1
                    # small sleep to be gentle
                    time.sleep(0.1)

            # 3) finish
            params_finish = {
                "upload_phase": "finish",
                "upload_session_id": upload_session_id,
                "access_token": self.access_token
            }
            # optionally include title/description in finish
            if title:
                params_finish["title"] = title
            if description:
                params_finish["description"] = description

            res_finish = requests.post(url, params=params_finish, timeout=60)
            try:
                res_finish.raise_for_status()
            except requests.RequestException as e:
                text = getattr(e.response, "text", None) if hasattr(e, "response") else None
                return {"error": "Finish failed", "response": text}
            return res_finish.json()

        except requests.RequestException as e:
            text = getattr(e.response, "text", None) if hasattr(e, "response") else None
            return {"error": str(e), "response": text}
        except Exception as e:
            return {"error": str(e)}

    # ---------------------------
    # Post video (automatic choose method by file size)
    # ---------------------------
    def post_video(self, video_path: str, title: str = "", description: str = "") -> dict:
        """
        Uploads a video to the Page. If file smaller than threshold uses direct upload,
        otherwise uses resumable upload.
        Returns Facebook response dict or error dict.
        """
        try:
            file_size = os.path.getsize(video_path)
        except Exception as e:
            return {"error": f"Cannot access video file: {e}"}

        # threshold (use resumable for > 50 MB)
        threshold = int(os.getenv("FB_VIDEO_RESUMABLE_THRESHOLD", 50 * 1024 * 1024))

        if file_size <= threshold:
            return self.post_video_direct(video_path, title=title, description=description)
        else:
            return self.post_video_resumable(video_path, title=title, description=description)

    # ---------------------------
    # Get page info
    # ---------------------------
    def get_page_info(self) -> dict:
        """Lấy thông tin cơ bản của Page."""
        url = self.base_url
        params = {"fields": "id,name,about,fan_count", "access_token": self.access_token}
        return self._get(url, params=params)

    # ---------------------------
    # High-level run (backwards-compatible)
    # ---------------------------
    def run(self, caption: str, short_post: str, image_path: str = None, video_path: str = None) -> dict:
        """
        Nhận caption và short_post → đăng Facebook.
        Prioritize video if video_path provided; otherwise post image if image_path provided; else post text.
        Trả về dict với published, result, message.
        """
        fb_content = f"{caption}\n\n{short_post}"
        try:
            result = None
            if video_path:
                # Try to upload video. You can pass caption as description/title
                video_title = caption if caption else ""
                video_description = short_post if short_post else ""
                result = self.post_video(video_path, title=video_title, description=video_description)
            elif image_path:
                result = self.post_photo(image_path, caption=fb_content)
            else:
                result = self.post_message(fb_content)

            # Interpret result
            if not isinstance(result, dict):
                # unexpected response
                return {"published": False, "result": result, "message": f"❌ Unexpected response type: {type(result)}"}

            if "error" in result:
                published = False
                msg_text = f"❌ Failed to publish: {result.get('error')}"
            elif "id" in result:
                published = True
                # For video upload, FB returns "id" of the published post or video id
                msg_text = f"✅ Published to Facebook (id={result.get('id')})"
            else:
                published = False
                msg_text = f"❌ Unknown response from Facebook: {result}"

        except Exception as e:
            published = False
            result = {"error": str(e)}
            msg_text = f"❌ Exception while publishing: {e}"

        print(msg_text)
        return {
            "published": published,
            "result": result,
            "message": msg_text
        }
