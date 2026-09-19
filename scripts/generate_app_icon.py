"""Generate multi-size JU-TAN Office application icon (JT monogram)."""

from __future__ import annotations

import struct
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "resources" / "app.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]


def make(size: int) -> Image.Image:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = max(1, size // 16)
    radius = max(2, size // 5)
    d.rounded_rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        radius=radius,
        fill=(11, 18, 32, 255),
    )
    bar_h = max(2, size // 10)
    d.rounded_rectangle(
        [
            pad + size // 8,
            size - pad - bar_h - size // 16,
            size - pad - size // 8,
            size - pad - size // 16,
        ],
        radius=max(1, bar_h // 2),
        fill=(5, 150, 105, 255),
    )
    font = None
    for name in ("segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"):
        try:
            font = ImageFont.truetype(name, max(8, int(size * 0.42)))
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    text = "JT"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1] - size * 0.06
    d.text((x, y), text, font=font, fill=(248, 250, 252, 255))
    return im


def _png_bytes(im: Image.Image) -> bytes:
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def write_ico(path: Path, images: list[Image.Image], sizes: list[int]) -> None:
    """Write a multi-size ICO with embedded PNG frames (Vista+)."""
    pngs = [_png_bytes(im) for im in images]
    count = len(sizes)
    header = struct.pack("<HHH", 0, 1, count)
    entries: list[bytes] = []
    offset = 6 + 16 * count
    blobs: list[bytes] = []
    for size, data in zip(sizes, pngs):
        w = 0 if size >= 256 else size
        h = 0 if size >= 256 else size
        entries.append(struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset))
        blobs.append(data)
        offset += len(data)
    path.write_bytes(header + b"".join(entries) + b"".join(blobs))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    images = [make(s) for s in SIZES]
    write_ico(OUT, images, SIZES)
    images[-1].save(OUT.with_suffix(".png"))
    print("wrote", OUT, OUT.stat().st_size, "sizes", SIZES)


if __name__ == "__main__":
    main()
