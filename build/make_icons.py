"""Generate PWA icons (PNG) from the izoh.uz-style book logo."""
from PIL import Image, ImageDraw
import pathlib

OUT = pathlib.Path(r"C:\izoh\icons")
OUT.mkdir(parents=True, exist_ok=True)

# Colors from izoh.uz logo
BROWN = (165, 42, 42)
TAN = (242, 200, 162)


def draw_icon(size: int, maskable: bool = False) -> Image.Image:
    """Draw the brown-square book icon at given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if maskable:
        # Maskable: brown fills whole square (safe-zone friendly)
        d.rectangle([(0, 0), (size, size)], fill=BROWN)
        # Lines are smaller (centered within 80% safe zone)
        inset = int(size * 0.20)
    else:
        # Regular: rounded square
        radius = int(size * 0.15)
        d.rounded_rectangle([(0, 0), (size, size)], radius=radius, fill=BROWN)
        inset = int(size * 0.22)

    # Book lines (4 horizontal bars of varying widths)
    w = size - 2 * inset
    y = inset
    bar_h = max(2, int(size * 0.07))
    gap = max(2, int(size * 0.05))

    # 4 lines like izoh.uz logo: full, half, full, 80%
    widths = [1.0, 0.55, 1.0, 0.85]
    bar_heights = [int(size * 0.10), bar_h, bar_h, bar_h]

    for i, (frac, h) in enumerate(zip(widths, bar_heights)):
        bw = int(w * frac)
        d.rectangle([(inset, y), (inset + bw, y + h)], fill=TAN)
        y += h + gap

    return img


def main():
    targets = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-192-maskable.png", 192, True),
        ("icon-512-maskable.png", 512, True),
        ("apple-touch-icon.png", 180, False),
        ("favicon-32.png", 32, False),
        ("favicon-16.png", 16, False),
    ]
    for name, size, maskable in targets:
        img = draw_icon(size, maskable)
        path = OUT / name
        img.save(path, "PNG", optimize=True)
        print(f"  {path.name:<28} {size}x{size}  {path.stat().st_size/1024:.1f} KB")


if __name__ == "__main__":
    main()
