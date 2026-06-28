from __future__ import annotations
#!/usr/bin/env python3
"""
Auto-generate templates.json from folder structure.

Usage:
    python3 scripts/sync_templates.py

Folder structure expected:
    webapp/
        templates/          <- PPTX files organized by category
            General/
                classic.pptx
                1.pptx
            modern/
                dark_theme.pptx
            Biology/
                cell.pptx
        static/previews/    <- Preview images (same folder names)
            General/
                classic.png
                1.png
            modern/
                dark_theme.png

The script scans templates/ for .pptx files, matches them with
previews from static/previews/, and writes data/templates.json.

To add a new category:
    1. Create a folder in templates/ (e.g. templates/Medicine/)
    2. Drop your .pptx files there
    3. Create matching folder in static/previews/Medicine/
    4. Drop preview .png/.jpg files with same base names
    5. Run: python3 scripts/sync_templates.py
"""

import os
import json

WEBAPP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webapp")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
PREVIEWS_DIR = os.path.join(WEBAPP_DIR, "static", "previews")
OUTPUT_JSON = os.path.join(WEBAPP_DIR, "data", "templates.json")


def get_file_size_str(path):
    """Human-readable file size."""
    size = os.path.getsize(path)
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size // 1024} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def find_preview(category, base_name):
    """Find preview image for a template (supports .png, .jpg, .jpeg)."""
    preview_dir = os.path.join(PREVIEWS_DIR, category)
    if not os.path.isdir(preview_dir):
        return None
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        path = os.path.join(preview_dir, base_name + ext)
        if os.path.exists(path):
            return f"static/previews/{category}/{base_name}{ext}"
    return None


def sync():
    templates = []

    if not os.path.isdir(TEMPLATES_DIR):
        print(f"❌ Templates directory not found: {TEMPLATES_DIR}")
        return

    categories = sorted(os.listdir(TEMPLATES_DIR))
    for category in categories:
        cat_path = os.path.join(TEMPLATES_DIR, category)
        if not os.path.isdir(cat_path) or category.startswith("."):
            continue

        pptx_files = sorted([f for f in os.listdir(cat_path) if f.endswith(".pptx")])
        
        for fname in pptx_files:
            base_name = os.path.splitext(fname)[0]
            file_path = os.path.join(cat_path, fname)
            
            # Generate a clean ID
            template_id = f"{category.lower()}_{base_name.lower().replace(' ', '_')}"
            
            # Find preview
            preview = find_preview(category, base_name)
            if not preview:
                preview = f"https://via.placeholder.com/200x120/1c1c1e/fff?text={base_name}"
            
            # Clean display name
            display_name = base_name.replace("_", " ").title()

            templates.append({
                "id": template_id,
                "name": display_name,
                "category": category,
                "preview": preview,
                "file_path": f"templates/{category}/{fname}",
                "file_size": get_file_size_str(file_path),
            })
        
        if not pptx_files:
            # Add a dummy entry to keep the category visible
            templates.append({
                "id": f"dummy_{category.lower()}",
                "name": "Tez orada...",
                "category": category,
                "preview": f"https://via.placeholder.com/200x120/1c1c1e/fff?text={category}",
                "file_path": "",
                "file_size": "0 KB",
                "is_empty": True
            })
            print(f"  📂 {category}: (empty — add .pptx files here)")
        else:
            print(f"  ✅ {category}: {len(pptx_files)} templates")

    # Write JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Generated {OUTPUT_JSON}")
    print(f"   Total: {len(templates)} templates in {len(set(t['category'] for t in templates))} categories")


if __name__ == "__main__":
    sync()
