from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "static" / "img" / "pwa"


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    return mask


def render_icon(size: int, destination: Path) -> None:
    canvas = Image.new("RGBA", (size, size), "#ffffff")
    safe = int(size * 0.08)
    shape_size = size - safe * 2
    radius = int(shape_size * 0.24)

    tile = Image.new("RGBA", (shape_size, shape_size), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)
    tile_draw.rounded_rectangle((0, 0, shape_size, shape_size), radius=radius, fill="#1c1c1e")

    stripe_w = max(10, int(shape_size * 0.12))
    top_h = max(16, int(shape_size * 0.26))
    top_y = int(shape_size * 0.14)
    center_x = shape_size // 2
    stripe_x = center_x - stripe_w // 2
    stripe_bottom = int(shape_size * 0.72)
    stripe = (255, 255, 255, 255)

    tile_draw.rounded_rectangle(
        (stripe_x, top_y, stripe_x + stripe_w, stripe_bottom),
        radius=max(4, stripe_w // 2),
        fill=stripe,
    )
    tile_draw.rounded_rectangle(
        (int(shape_size * 0.2), top_y, int(shape_size * 0.8), top_y + top_h),
        radius=max(6, top_h // 2),
        fill=stripe,
    )

    dash_w = max(8, stripe_w // 3)
    dash_h = max(12, int(shape_size * 0.08))
    dash_gap = dash_h
    dash_x = center_x - dash_w // 2
    first_dash_y = int(shape_size * 0.34)
    for index in range(3):
        y = first_dash_y + index * (dash_h + dash_gap)
        tile_draw.rounded_rectangle(
            (dash_x, y, dash_x + dash_w, y + dash_h),
            radius=dash_w // 2,
            fill="#1c1c1e",
        )

    dot_size = max(22, int(shape_size * 0.2))
    dot_x = int(shape_size * 0.62)
    dot_y = int(shape_size * 0.63)
    tile_draw.ellipse((dot_x, dot_y, dot_x + dot_size, dot_y + dot_size), fill="#f5c518")
    inner = max(8, dot_size // 3)
    inner_x = dot_x + (dot_size - inner) // 2
    inner_y = dot_y + (dot_size - inner) // 2
    tile_draw.ellipse((inner_x, inner_y, inner_x + inner, inner_y + inner), fill="#ffffff")

    shadow = Image.new("RGBA", (shape_size, shape_size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((0, 0, shape_size, shape_size), radius=radius, fill=(0, 0, 0, 34))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(2, size // 64)))
    canvas.alpha_composite(shadow, (safe, safe + max(4, size // 48)))
    canvas.alpha_composite(tile, (safe, safe))

    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="PNG")


def render_maskable_icon(size: int, destination: Path) -> None:
    canvas = Image.new("RGBA", (size, size), "#1c1c1e")
    draw = ImageDraw.Draw(canvas)
    road_x = size // 2
    stripe_w = max(16, size // 10)
    top_h = max(28, size // 5)
    draw.rounded_rectangle(
        (road_x - stripe_w // 2, int(size * 0.12), road_x + stripe_w // 2, int(size * 0.78)),
        radius=stripe_w // 2,
        fill="#ffffff",
    )
    draw.rounded_rectangle(
        (int(size * 0.18), int(size * 0.12), int(size * 0.82), int(size * 0.12) + top_h),
        radius=top_h // 2,
        fill="#ffffff",
    )
    dot_size = max(44, size // 5)
    dot_x = int(size * 0.61)
    dot_y = int(size * 0.63)
    draw.ellipse((dot_x, dot_y, dot_x + dot_size, dot_y + dot_size), fill="#f5c518")
    inner = max(16, dot_size // 3)
    inner_x = dot_x + (dot_size - inner) // 2
    inner_y = dot_y + (dot_size - inner) // 2
    draw.ellipse((inner_x, inner_y, inner_x + inner, inner_y + inner), fill="#ffffff")
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="PNG")


def main() -> int:
    render_icon(192, OUTPUT_DIR / "icon-192.png")
    render_icon(512, OUTPUT_DIR / "icon-512.png")
    render_maskable_icon(512, OUTPUT_DIR / "icon-maskable-512.png")
    render_icon(180, OUTPUT_DIR / "apple-touch-icon-180.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
