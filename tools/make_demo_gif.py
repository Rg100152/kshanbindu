"""Build static/assets/demo-preview.gif from the two real Flask screenshots.

Usage: python3 tools/make_demo_gif.py
Requires Pillow (pip install pillow). The GIF is generated with a soft
Ken Burns zoom and a crossfade between the booking studio and the dashboard.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "static" / "assets"
SIZE = (960, 700)


def load(name: str) -> Image.Image:
    return Image.open(ASSETS / name).convert("RGB").resize(SIZE, Image.Resampling.LANCZOS)


def zoom(image: Image.Image, factor: float) -> Image.Image:
    w, h = image.size
    nw, nh = int(w * factor), int(h * factor)
    scaled = image.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - w) // 2, (nh - h) // 2
    return scaled.crop((left, top, left + w, top + h))


def caption(image: Image.Image, text: str) -> Image.Image:
    frame = image.copy()
    draw = ImageDraw.Draw(frame)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    try:
        font = ImageFont.truetype(str(font_path), 20)
    except OSError:
        font = ImageFont.load_default()
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    x, y = 26, SIZE[1] - th - 38
    draw.rounded_rectangle((x - 14, y - 10, x + tw + 14, y + th + 12), radius=10, fill=(15, 23, 42))
    draw.text((x, y - 2), text, font=font, fill=(248, 250, 252))
    return frame


def main() -> None:
    booking = load("screenshot-booking.png")
    dashboard = load("screenshot-dashboard.png")
    frames = []

    for index in range(14):
        factor = 1.0 + 0.0025 * index
        frames.append(caption(zoom(booking, factor), "01  ·  BOOK A MOMENT"))

    for index in range(10):
        alpha = (index + 1) / 11
        frames.append(caption(Image.blend(booking, dashboard, alpha), "02  ·  HOST DASHBOARD + SMART REMINDERS"))

    for index in range(12):
        factor = 1.03 - 0.0015 * index
        frames.append(caption(zoom(dashboard, factor), "02  ·  HOST DASHBOARD + SMART REMINDERS"))

    palette = [frame.quantize(colors=160, method=Image.Quantize.FASTOCTREE) for frame in frames]
    output = ASSETS / "demo-preview.gif"
    palette[0].save(
        output,
        save_all=True,
        append_images=palette[1:],
        duration=110,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"✓ wrote {output} ({len(palette)} frames, {output.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
