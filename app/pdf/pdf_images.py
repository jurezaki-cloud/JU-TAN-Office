from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import Image, Spacer


def pdf_image(path: str, max_width_mm: float = 42, max_height_mm: float = 22):
    if not path or not Path(path).exists():
        return None
    try:
        image = Image(path)
    except Exception:
        return None
    max_w = max_width_mm * mm
    max_h = max_height_mm * mm
    width = float(image.imageWidth or 1)
    height = float(image.imageHeight or 1)
    scale = min(max_w / width, max_h / height, 1.0)
    image.drawWidth = width * scale
    image.drawHeight = height * scale
    return image


def image_or_space(path: str, width_mm: float, height_mm: float):
    image = pdf_image(path, width_mm, height_mm)
    if image is not None:
        return image
    return Spacer(width_mm * mm, height_mm * mm)
