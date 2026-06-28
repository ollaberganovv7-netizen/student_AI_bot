from __future__ import annotations
"""Generate preview PNG images for template categories."""
from PIL import Image, ImageDraw, ImageFont
import os

CATEGORIES = {
    "Biology": {"color": (46, 125, 50), "bg": (241, 248, 233)},
    "Medicine": {"color": (21, 101, 192), "bg": (227, 242, 253)},
    "Business": {"color": (55, 71, 79), "bg": (236, 239, 241)},
    "IT": {"color": (106, 27, 154), "bg": (243, 229, 245)},
    "History": {"color": (191, 54, 12), "bg": (251, 233, 231)},
    "Buxgalteriya": {"color": (0, 105, 92), "bg": (224, 242, 241)},
}

TEMPLATES = {
    "Biology": ["nature_green", "cell_light"],
    "Medicine": ["medical_blue", "health_clean"],
    "Business": ["corporate_dark", "business_minimal"],
    "IT": ["tech_purple", "code_dark"],
    "History": ["vintage_warm", "history_classic"],
    "Buxgalteriya": ["finance_teal", "accounting_clean"],
}

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
preview_dir = os.path.join(base, "webapp", "static", "previews")

for cat, styles in TEMPLATES.items():
    cat_dir = os.path.join(preview_dir, cat)
    os.makedirs(cat_dir, exist_ok=True)

    for idx, name in enumerate(styles):
        cfg = CATEGORIES[cat]
        is_dark = idx == 1

        w, h = 800, 450
        if is_dark:
            img = Image.new("RGB", (w, h), (30, 30, 46))
            text_color = (255, 255, 255)
        else:
            img = Image.new("RGB", (w, h), cfg["bg"])
            text_color = cfg["color"]

        draw = ImageDraw.Draw(img)

        # Accent bar on left
        draw.rectangle([0, 0, 8, h], fill=cfg["color"])
        # Top accent line
        draw.rectangle([0, 0, w, 5], fill=cfg["color"])

        # Category name
        try:
            font_big = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            font_sm = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except Exception:
            font_big = ImageFont.load_default()
            font_sm = ImageFont.load_default()

        draw.text((w // 2, h // 2 - 40), cat, fill=text_color, font=font_big, anchor="mm")
        label = name.replace("_", " ").title()
        draw.text((w // 2, h // 2 + 30), label, fill=text_color, font=font_sm, anchor="mm")

        # Bottom accent bar
        draw.rectangle([0, h - 5, w, h], fill=cfg["color"])

        path = os.path.join(cat_dir, f"{name}.png")
        img.save(path)
        print(f"  OK {cat}/{name}.png")

print("Done!")
