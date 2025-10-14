# --- aggregate_embeddings inline (không cần API) ---
from PIL import Image
import io
import torch
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1

device = 'cuda' if torch.cuda.is_available() else 'cpu'

_mtcnn = MTCNN(keep_all=True, device=device)
_resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

def l2_normalize_tensor(t: torch.Tensor, eps=1e-10):
    return t / (t.norm(p=2) + eps)

def _pil_from_input(inp):
    if isinstance(inp, Image.Image):
        return inp.convert('RGB')
    if isinstance(inp, (bytes, bytearray)):
        return Image.open(io.BytesIO(inp)).convert('RGB')
    if isinstance(inp, str):
        return Image.open(inp).convert('RGB')
    raise ValueError("Unsupported image input type.")

def _get_best_face_tensor(pil_img: Image.Image):
    boxes, probs = _mtcnn.detect(pil_img)
    if boxes is None or len(boxes) == 0:
        return None, "no_face"

    best_idx = int(np.argmax(probs)) if probs is not None else 0
    box = boxes[best_idx]
    x1, y1, x2, y2 = box
    pad = 0.25 * max(x2 - x1, y2 - y1)
    x1, y1, x2, y2 = max(0, int(x1 - pad)), max(0, int(y1 - pad)), int(x2 + pad), int(y2 + pad)
    crop = pil_img.crop((x1, y1, x2, y2))

    try:
        face_tensor = _mtcnn._preprocess(crop)
    except Exception:
        face_tensor = _mtcnn(crop)
        if face_tensor is None:
            return None, "preprocess_failed"
        if face_tensor.ndim == 4:
            face_tensor = face_tensor[0]
    return face_tensor, "ok"

def aggregate_embeddings(images, save_path=None):
    embeddings = []
    for img_path in images:
        pil = _pil_from_input(img_path)
        face_tensor, status = _get_best_face_tensor(pil)
        if face_tensor is None:
            print(f"⚠️  {img_path}: {status}")
            continue
        face_tensor = face_tensor.unsqueeze(0).to(device)
        with torch.no_grad():
            emb = _resnet(face_tensor)
        emb = emb.squeeze(0).cpu()
        emb = l2_normalize_tensor(emb)
        embeddings.append(emb)

    if not embeddings:
        raise RuntimeError("❌ No faces detected.")
    agg = torch.stack(embeddings).mean(dim=0)
    agg = l2_normalize_tensor(agg)
    if save_path:
        np.save(save_path, agg.cpu().numpy())
        print(f"✅ Saved embedding to {save_path}")
    return agg

# ---- chạy để tạo embed ----
image_list = [f"img/refs/{i}.jpg" for i in range(1, 11)]  # thay bằng đường dẫn thật
final_embed = aggregate_embeddings(image_list, save_path="faceid_embed.npy")

print("✅ Embed shape:", final_embed.shape)
