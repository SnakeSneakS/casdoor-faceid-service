from __future__ import annotations

import base64
import binascii


def decode_base64_image(value: str, max_bytes: int):
    """Decode a base64 image or data URL into an OpenCV BGR image."""
    if not value:
        raise ValueError("image is empty")

    if "," in value and value.lstrip().startswith("data:"):
        value = value.split(",", 1)[1]

    try:
        raw = base64.b64decode(value, validate=False)
    except binascii.Error as exc:
        raise ValueError("image is not valid base64") from exc

    if len(raw) > max_bytes:
        raise ValueError("image exceeds maximum size")

    import cv2
    import numpy as np

    buffer = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("image cannot be decoded")
    return image
