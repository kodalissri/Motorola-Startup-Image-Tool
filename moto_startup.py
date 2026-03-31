"""
MOTOTRBO Startup Image Converter
Converts any image to the correct BMP format for Motorola MOTOTRBO radios.

Usage:
    python moto_startup.py <input_image> <model> [--output <path>] [--preview]

Models: xpr5550, xpr7550, xpr7350, sl7550, r7

Examples:
    python moto_startup.py logo.png xpr7550
    python moto_startup.py logo.jpg r7 --output my_splash.bmp
    python moto_startup.py logo.png all          # generate for ALL models
    python moto_startup.py logo.png xpr7550 --preview
"""

import argparse
import struct
import sys
from pathlib import Path

from PIL import Image

# ── Radio model specifications ───────────────────────────────────────────────
MODELS = {
    "xpr5550": {
        "name": "XPR 5550 / 5550e (Mobile)",
        "width": 160,
        "height": 72,
        "depth": 8,  # 8-bit indexed (256 colors)
    },
    "xpr7550": {
        "name": "XPR 7550 / 7550e (Portable)",
        "width": 132,
        "height": 90,
        "depth": 8,
    },
    "xpr7350": {
        "name": "XPR 7350e (Portable Mono)",
        "width": 132,
        "height": 72,
        "depth": 1,  # 1-bit monochrome
    },
    "hch": {
        "name": "Handheld Control Head (HCH)",
        "width": 132,
        "height": 90,
        "depth": 8,  # 256 color (same as portable full keypad)
    },
    "sl7550": {
        "name": "SL7550 / SL300",
        "width": 320,
        "height": 240,
        "depth": 16,  # 16-bit RGB565
    },
    "r7": {
        "name": "MOTOTRBO R7",
        "width": 240,
        "height": 320,
        "depth": 16,
    },
}

MODEL_ALIASES = {
    "xpr5000": "xpr5550",
    "xpr5550e": "xpr5550",
    "dm4400": "xpr5550",
    "dm4400e": "xpr5550",
    "xpr7550e": "xpr7550",
    "dp4800": "xpr7550",
    "dp4800e": "xpr7550",
    "dp3661e": "xpr7550",
    "xpr7350e": "xpr7350",
    "dp4600": "xpr7350",
    "sl300": "sl7550",
    "sl4000": "sl7550",
    "sl4000e": "sl7550",
}


def resolve_model(name: str) -> str:
    key = name.lower().replace(" ", "").replace("-", "")
    if key in MODELS:
        return key
    if key in MODEL_ALIASES:
        return MODEL_ALIASES[key]
    return None


def resize_and_fit(img: Image.Image, w: int, h: int) -> Image.Image:
    """Resize image to fit target dimensions, preserving aspect ratio with
    letterboxing (black fill) if needed."""
    img = img.convert("RGBA")
    # Calculate scale to fit within target
    scale = min(w / img.width, h / img.height)
    new_w = int(img.width * scale)
    new_h = int(img.height * scale)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Create black background and paste centered
    canvas = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    x_offset = (w - new_w) // 2
    y_offset = (h - new_h) // 2
    canvas.paste(resized, (x_offset, y_offset), resized)
    return canvas.convert("RGB")


def save_8bit_bmp(img: Image.Image, output: Path):
    """Save as 8-bit (256 color) indexed BMP."""
    quantized = img.quantize(colors=256, method=Image.MEDIANCUT)
    quantized.save(str(output), format="BMP")


def save_1bit_bmp(img: Image.Image, output: Path):
    """Save as 1-bit monochrome BMP."""
    mono = img.convert("1")
    mono.save(str(output), format="BMP")


def save_16bit_rgb565_bmp(img: Image.Image, output: Path):
    """Save as 16-bit RGB565 BMP (manual construction).
    Pillow can't export RGB565 natively, so we build the file by hand."""
    w, h = img.size
    pixels = img.load()

    # BMP rows are padded to 4-byte boundaries
    row_bytes = w * 2  # 2 bytes per pixel (16-bit)
    row_padding = (4 - (row_bytes % 4)) % 4
    padded_row = row_bytes + row_padding

    pixel_data_size = padded_row * h
    header_size = 14  # BMP file header
    dib_size = 40     # BITMAPINFOHEADER
    # RGB565 needs 3 x 4-byte color masks after the DIB header
    masks_size = 12
    offset = header_size + dib_size + masks_size
    file_size = offset + pixel_data_size

    bmp = bytearray()

    # ── BMP File Header (14 bytes) ───────────────────────────────────────
    bmp += b"BM"
    bmp += struct.pack("<I", file_size)
    bmp += struct.pack("<HH", 0, 0)  # reserved
    bmp += struct.pack("<I", offset)

    # ── DIB Header (BITMAPINFOHEADER, 40 bytes) ──────────────────────────
    bmp += struct.pack("<I", dib_size)
    bmp += struct.pack("<i", w)
    bmp += struct.pack("<i", h)  # positive = bottom-up
    bmp += struct.pack("<HH", 1, 16)  # planes=1, bpp=16
    bmp += struct.pack("<I", 3)  # compression = BI_BITFIELDS
    bmp += struct.pack("<I", pixel_data_size)
    bmp += struct.pack("<i", 2835)  # ~72 DPI horizontal
    bmp += struct.pack("<i", 2835)  # ~72 DPI vertical
    bmp += struct.pack("<I", 0)  # colors used
    bmp += struct.pack("<I", 0)  # important colors

    # ── Color masks (R5 G6 B5) ───────────────────────────────────────────
    bmp += struct.pack("<I", 0xF800)  # Red mask:   1111100000000000
    bmp += struct.pack("<I", 0x07E0)  # Green mask: 0000011111100000
    bmp += struct.pack("<I", 0x001F)  # Blue mask:  0000000000011111

    # ── Pixel data (bottom-up) ───────────────────────────────────────────
    for y in range(h - 1, -1, -1):
        row = bytearray()
        for x in range(w):
            r, g, b = pixels[x, y]
            r5 = (r >> 3) & 0x1F
            g6 = (g >> 2) & 0x3F
            b5 = (b >> 3) & 0x1F
            pixel = (r5 << 11) | (g6 << 5) | b5
            row += struct.pack("<H", pixel)
        row += b"\x00" * row_padding
        bmp += row

    output.write_bytes(bytes(bmp))


def convert_image(input_path: str, model_key: str, output_path: str = None, preview: bool = False) -> str:
    """Convert an image for the specified radio model. Returns the output path."""
    spec = MODELS[model_key]
    w, h, depth = spec["width"], spec["height"], spec["depth"]

    img = Image.open(input_path)
    fitted = resize_and_fit(img, w, h)

    if output_path is None:
        stem = Path(input_path).stem
        output_path = str(Path(input_path).parent / f"{stem}_{model_key}.bmp")
    out = Path(output_path)

    if depth == 8:
        save_8bit_bmp(fitted, out)
    elif depth == 1:
        save_1bit_bmp(fitted, out)
    elif depth == 16:
        save_16bit_rgb565_bmp(fitted, out)

    if preview:
        fitted.show()

    return str(out)


def list_models():
    print("\nSupported MOTOTRBO Radio Models:\n")
    print(f"  {'Key':<12} {'Model':<32} {'Size':<12} {'Depth'}")
    print(f"  {'---':<12} {'-----':<32} {'----':<12} {'-----'}")
    for key, spec in MODELS.items():
        size = f"{spec['width']}x{spec['height']}"
        depth = f"{spec['depth']}-bit"
        if spec["depth"] == 16:
            depth += " (RGB565)"
        elif spec["depth"] == 1:
            depth += " (mono)"
        else:
            depth += " (indexed)"
        print(f"  {key:<12} {spec['name']:<32} {size:<12} {depth}")

    print("\n  Aliases:")
    for alias, target in sorted(MODEL_ALIASES.items()):
        print(f"    {alias} -> {target}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="MOTOTRBO Startup Image Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", nargs="?", help="Input image file (PNG, JPG, BMP, etc.)")
    parser.add_argument("model", nargs="?", help="Radio model key (e.g. xpr7550, r7, all)")
    parser.add_argument("-o", "--output", help="Output BMP file path (auto-generated if omitted)")
    parser.add_argument("--preview", action="store_true", help="Show preview of the converted image")
    parser.add_argument("--list", action="store_true", help="List all supported models and exit")

    args = parser.parse_args()

    if args.list:
        list_models()
        return

    if not args.input or not args.model:
        parser.print_help()
        return

    input_path = args.input
    if not Path(input_path).exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    # Handle "all" to generate for every model
    if args.model.lower() == "all":
        print(f"\nConverting '{input_path}' for all models...\n")
        for key, spec in MODELS.items():
            out = convert_image(input_path, key, preview=args.preview)
            size = f"{spec['width']}x{spec['height']}"
            print(f"  {spec['name']:<32} {size:<12} -> {out}")
        print("\nDone! All files saved.")
        return

    model_key = resolve_model(args.model)
    if model_key is None:
        print(f"Error: Unknown model '{args.model}'")
        print("Use --list to see supported models, or use 'all' to generate for every model.")
        sys.exit(1)

    spec = MODELS[model_key]
    out = convert_image(input_path, model_key, args.output, args.preview)
    size = f"{spec['width']}x{spec['height']}"
    depth = spec["depth"]
    print(f"\nConverted for {spec['name']}")
    print(f"  Size:   {size}")
    print(f"  Depth:  {depth}-bit {'RGB565' if depth == 16 else 'indexed' if depth == 8 else 'mono'}")
    print(f"  Output: {out}")


if __name__ == "__main__":
    main()
