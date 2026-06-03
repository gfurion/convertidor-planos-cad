"""Generate a simple .ico icon for the Convertidor de Planos CAD app."""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(output_path):
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background rounded rect (dark blue - matches "superhero" theme)
    margin = 8
    draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=32,
        fill=(20, 60, 120, 255),
        outline=(60, 140, 220, 255),
        width=4
    )

    # Inner lighter circle
    cx = cy = size // 2
    r1 = 70
    draw.ellipse(
        [cx - r1, cy - r1, cx + r1, cy + r1],
        fill=(30, 80, 160, 255),
        outline=(80, 170, 240, 255),
        width=3
    )

    # Text "C C A D" in two lines: "CAD" large, "CC" smaller above
    try:
        font_large = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 72)
        font_small = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 36)
    except OSError:
        try:
            font_large = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 72)
            font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
        except OSError:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

    # "CAD" large
    text1 = "CAD"
    bbox1 = draw.textbbox((0, 0), text1, font=font_large)
    tw1 = bbox1[2] - bbox1[0]
    th1 = bbox1[3] - bbox1[1]
    tx1 = (size - tw1) // 2
    ty1 = (size - th1) // 2 + 10

    # "CC" small, above "CAD"
    text2 = "CC"
    bbox2 = draw.textbbox((0, 0), text2, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    th2 = bbox2[3] - bbox2[1]
    tx2 = (size - tw2) // 2
    ty2 = ty1 - th2 - 5

    draw.text((tx2, ty2), text2, fill=(200, 230, 255, 255), font=font_small)
    draw.text((tx1, ty1), text1, fill=(255, 255, 255, 255), font=font_large)

    # Save as multi-resolution ICO
    sizes = [16, 32, 48, 64, 128, 256]
    img.save(output_path, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Icono creado: {output_path}  ({os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.abspath(__file__))
    output = os.path.join(project_dir, "icono.ico")
    create_icon(output)
