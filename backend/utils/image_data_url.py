import base64
from typing import Optional, Tuple


def _normalize_image_mime(mime: str) -> str:
    text = str(mime or "").strip().lower()
    if text == "image/jpg":
        return "image/jpeg"
    return text


def guess_image_mime_from_bytes(raw: bytes) -> Optional[str]:
    if not raw:
        return None
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith(b"GIF87a") or raw.startswith(b"GIF89a"):
        return "image/gif"
    if raw.startswith(b"BM"):
        return "image/bmp"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


def parse_image_data_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(url, str) or not url.startswith("data:"):
        return None, None
    try:
        header, b64 = url.split(",", 1)
    except ValueError:
        return None, None

    mime = header[5:].split(";", 1)[0].strip() if header.startswith("data:") else ""
    mime = _normalize_image_mime(mime)
    if not mime or mime == "application/octet-stream":
        try:
            raw = base64.b64decode(b64, validate=False)
        except Exception:
            raw = b""
        guessed = guess_image_mime_from_bytes(raw)
        if guessed:
            mime = guessed
    if not mime:
        mime = "application/octet-stream"
    return mime, b64


def normalize_image_data_url(url: Optional[str]) -> Optional[str]:
    if not isinstance(url, str) or not url.startswith("data:"):
        return url
    mime, b64 = parse_image_data_url(url)
    if not mime or b64 is None:
        return url
    return f"data:{mime};base64,{b64}"
