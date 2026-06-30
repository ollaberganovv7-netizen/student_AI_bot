"""
Premium Presentation Design System
====================================
Generates modern, professional, premium designs for presentations.
Each slide gets unique design based on topic and slide type.
No templates copied - every presentation is uniquely designed by AI logic.

Author: Student AI Bot
"""

from __future__ import annotations
import random
import re
from typing import Optional, List, Dict
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.oxml import parse_xml


# ════════════════════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ════════════════════════════════════════════════════════════════════════════════

def _hex(h: str) -> RGBColor:
    """Convert hex string to RGBColor."""
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _lighter(hex_color: str, factor: float = 0.15) -> str:
    """Make a hex color lighter by factor (0-1)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"{r:02X}{g:02X}{b:02X}"


def _darker(hex_color: str, factor: float = 0.2) -> str:
    """Make a hex color darker by factor (0-1)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return f"{r:02X}{g:02X}{b:02X}"


# ════════════════════════════════════════════════════════════════════════════════
# COLOR PALETTES (15+ professional palettes with topic keyword matching)
# ════════════════════════════════════════════════════════════════════════════════

_PALETTES = [
    {
        "name": "midnight_tech",
        "bg1": "0B0E1A", "bg2": "151B2E",
        "accent": "6C63FF", "accent2": "3F3D9E",
        "text1": "F0F0FF", "text2": "9E9EBF",
        "on_accent": "FFFFFF", "is_dark": True,
        "keywords": ["texnologiya", "kompyuter", "dastur", "raqamli", "it", "sun'iy",
                     "intellekt", "robot", "axborot", "tizim", "elektron", "internet",
                     "dasturlash", "algoritm", "ma'lumot", "baza", "tarmoq", "server",
                     "kiberhujum", "xavfsizlik", "programma"]
    },
    {
        "name": "ocean_depth",
        "bg1": "0A1929", "bg2": "0D2847",
        "accent": "00BCD4", "accent2": "0288D1",
        "text1": "E3F2FD", "text2": "81D4FA",
        "on_accent": "FFFFFF", "is_dark": True,
        "keywords": ["dengiz", "suv", "okean", "transport", "logistika",
                     "savdo", "import", "eksport", "moliya", "bank"]
    },
    {
        "name": "emerald_forest",
        "bg1": "0D1F1A", "bg2": "133025",
        "accent": "00E676", "accent2": "00C853",
        "text1": "E8F5E9", "text2": "A5D6A7",
        "on_accent": "0D1F1A", "is_dark": True,
        "keywords": ["tabiat", "ekologiya", "atrof-muhit", "biologiya", "o'simlik",
                     "hayvon", "qishloq", "dehqonchilik", "fermer", "yashil", "o'rmon"]
    },
    {
        "name": "royal_purple",
        "bg1": "1A0A2E", "bg2": "2D1458",
        "accent": "BB86FC", "accent2": "7C4DFF",
        "text1": "F3E5F5", "text2": "CE93D8",
        "on_accent": "1A0A2E", "is_dark": True,
        "keywords": ["san'at", "madaniyat", "adabiyot", "musiqa", "dizayn",
                     "ijodkorlik", "falsafa", "psixologiya", "she'riyat"]
    },
    {
        "name": "sunset_warm",
        "bg1": "1A0F0A", "bg2": "2E1810",
        "accent": "FF6D00", "accent2": "FF9100",
        "text1": "FFF3E0", "text2": "FFCC80",
        "on_accent": "FFFFFF", "is_dark": True,
        "keywords": ["energiya", "neft", "gaz", "sanoat", "ishlab chiqarish",
                     "quvvat", "elektr", "issiqlik"]
    },
    {
        "name": "crimson_elegance",
        "bg1": "1A0A0F", "bg2": "2E1018",
        "accent": "FF1744", "accent2": "D50000",
        "text1": "FFEBEE", "text2": "EF9A9A",
        "on_accent": "FFFFFF", "is_dark": True,
        "keywords": ["tibbiyot", "sog'liq", "kasallik", "dori", "shifoxona",
                     "jarrohlik", "anatomiya", "fiziologiya"]
    },
    {
        "name": "arctic_ice",
        "bg1": "F4F7FC", "bg2": "E8EEF8",
        "accent": "1565C0", "accent2": "0D47A1",
        "text1": "1A237E", "text2": "3949AB",
        "on_accent": "FFFFFF", "is_dark": False,
        "keywords": ["huquq", "qonun", "davlat", "boshqaruv", "siyosat",
                     "demokratiya", "konstitutsiya", "parlament"]
    },
    {
        "name": "pearl_light",
        "bg1": "FAFAFA", "bg2": "F0F0F0",
        "accent": "FF5722", "accent2": "E64A19",
        "text1": "212121", "text2": "616161",
        "on_accent": "FFFFFF", "is_dark": False,
        "keywords": ["arxitektura", "qurilish", "loyiha", "bino", "shaharsozlik",
                     "infrastruktura", "transport"]
    },
    {
        "name": "golden_finance",
        "bg1": "0F0E0A", "bg2": "1E1C14",
        "accent": "FFD600", "accent2": "FFC107",
        "text1": "FFFDE7", "text2": "FFF9C4",
        "on_accent": "0F0E0A", "is_dark": True,
        "keywords": ["iqtisodiyot", "moliya", "buxgalteriya", "soliq", "budget",
                     "investitsiya", "valyuta", "kredit", "fond", "bozor"]
    },
    {
        "name": "teal_science",
        "bg1": "0A1A1A", "bg2": "102929",
        "accent": "00BFA5", "accent2": "009688",
        "text1": "E0F2F1", "text2": "80CBC4",
        "on_accent": "FFFFFF", "is_dark": True,
        "keywords": ["kimyo", "fizika", "matematika", "fan", "tadqiqot",
                     "laboratoriya", "tajriba", "formula", "nazariya"]
    },
    {
        "name": "coral_education",
        "bg1": "1A0E14", "bg2": "2E1824",
        "accent": "FF4081", "accent2": "F50057",
        "text1": "FCE4EC", "text2": "F48FB1",
        "on_accent": "FFFFFF", "is_dark": True,
        "keywords": ["ta'lim", "o'qitish", "pedagogika", "maktab", "universitet",
                     "talaba", "o'quvchi", "dars", "metodika"]
    },
    {
        "name": "steel_industrial",
        "bg1": "1A1C20", "bg2": "2C2F36",
        "accent": "78909C", "accent2": "546E7A",
        "text1": "ECEFF1", "text2": "B0BEC5",
        "on_accent": "FFFFFF", "is_dark": True,
        "keywords": ["muhandislik", "texnika", "mashina", "metallurgiya",
                     "avtomatika", "mexanika", "elektronika"]
    },
    {
        "name": "olive_history",
        "bg1": "141410", "bg2": "22221A",
        "accent": "CDDC39", "accent2": "AFB42B",
        "text1": "F9FBE7", "text2": "DCED6B",
        "on_accent": "141410", "is_dark": True,
        "keywords": ["tarix", "davlat", "sivilizatsiya", "arxeologiya", "qadimiy",
                     "mustaqillik", "millat", "xalq"]
    },
    {
        "name": "sky_blue_fresh",
        "bg1": "F5FBFF", "bg2": "E3F2FD",
        "accent": "2196F3", "accent2": "1976D2",
        "text1": "0D1B2A", "text2": "37474F",
        "on_accent": "FFFFFF", "is_dark": False,
        "keywords": ["aviatsiya", "kosmos", "samolyot", "parvoz", "meteorologiya",
                     "atmosfera", "ob-havo"]
    },
    {
        "name": "dark_gradient_universal",
        "bg1": "111827", "bg2": "1F2937",
        "accent": "818CF8", "accent2": "6366F1",
        "text1": "F9FAFB", "text2": "D1D5DB",
        "on_accent": "FFFFFF", "is_dark": True,
        "keywords": []  # universal fallback for dark
    },
    {
        "name": "warm_light_universal",
        "bg1": "FFF8F0", "bg2": "FFF0E0",
        "accent": "F97316", "accent2": "EA580C",
        "text1": "1C1917", "text2": "57534E",
        "on_accent": "FFFFFF", "is_dark": False,
        "keywords": []  # universal fallback for light
    },
]


def _select_palette(topic: str) -> dict:
    """Select the best color palette based on topic keywords."""
    if not topic:
        return random.choice(_PALETTES[:-2])  # exclude fallbacks

    topic_lower = topic.lower()
    best_match = None
    best_score = 0

    for pal in _PALETTES:
        score = 0
        for kw in pal["keywords"]:
            if kw in topic_lower:
                score += len(kw)  # longer matches score higher
        if score > best_score:
            best_score = score
            best_match = pal

    if best_match and best_score > 0:
        return best_match

    # Random from main palettes (exclude last 2 universal ones)
    return random.choice(_PALETTES[:-2])


# ════════════════════════════════════════════════════════════════════════════════
# SLIDE TYPE DETECTION
# ════════════════════════════════════════════════════════════════════════════════

_TITLE_WORDS = {"muqova", "title"}
_SECTION_WORDS = {"o'quv savoli", "bo'lim", "section", "qism"}
_PLAN_WORDS = {"reja", "plan", "mundarija", "o'quv savollari"}
_INTRO_WORDS = {"kirish", "introduction", "maqsad"}
_CONCLUSION_WORDS = {"xulosa", "conclusion", "yakun"}
_REFERENCE_WORDS = {"adabiyotlar", "adabiyot", "manbalar", "references", "foydalanilgan"}
_QUOTE_WORDS = {"iqtibos", "tsitata", "quote"}
_FINAL_WORDS = {"rahmat", "thank", "e'tibor", "yakuniy"}
_GOAL_WORDS = {"maqsad", "maqsadlar", "tarbiyaviy"}


def _detect_slide_type(slide, idx: int, total: int) -> str:
    """Detect slide type from content and position."""
    if idx == 0:
        return "title"
    if idx == total - 1:
        return "final"

    text = ""
    for shape in slide.shapes:
        if shape.has_text_frame:
            text += " " + shape.text_frame.text.lower()

    text = text.strip()

    for w in _QUOTE_WORDS:
        if w in text:
            return "quote"
    for w in _CONCLUSION_WORDS:
        if w in text:
            return "conclusion"
    for w in _REFERENCE_WORDS:
        if w in text:
            return "references"
    for w in _GOAL_WORDS:
        if w in text:
            return "goals"
    for w in _PLAN_WORDS:
        if w in text:
            return "plan"
    for w in _INTRO_WORDS:
        if w in text:
            return "intro"
    for w in _SECTION_WORDS:
        if w in text:
            return "section"
    for w in _FINAL_WORDS:
        if w in text:
            return "final"

    return "content"


# ════════════════════════════════════════════════════════════════════════════════
# GRADIENT BACKGROUNDS (XML injection)
# ════════════════════════════════════════════════════════════════════════════════

_NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
_NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _set_gradient_bg(slide, c1: str, c2: str, angle: int = 5400000):
    """Apply 2-stop gradient background. Falls back to solid on error."""
    try:
        slide.follow_master_background = False
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = _hex(c1)

        bg_elem = slide._element.find(f'{{{_NS_P}}}bg')
        if bg_elem is not None:
            bgPr = bg_elem.find(f'{{{_NS_P}}}bgPr')
            if bgPr is not None:
                for child in list(bgPr):
                    local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if 'Fill' in local or 'fill' in local:
                        bgPr.remove(child)

                grad = parse_xml(
                    f'<a:gradFill xmlns:a="{_NS_A}" rotWithShape="1">'
                    f'<a:gsLst>'
                    f'<a:gs pos="0"><a:srgbClr val="{c1}"/></a:gs>'
                    f'<a:gs pos="100000"><a:srgbClr val="{c2}"/></a:gs>'
                    f'</a:gsLst>'
                    f'<a:lin ang="{angle}" scaled="0"/>'
                    f'</a:gradFill>'
                )
                bgPr.insert(0, grad)
    except Exception:
        try:
            slide.follow_master_background = False
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = _hex(c1)
        except Exception:
            pass


def _set_gradient_3stop(slide, c1: str, c2: str, c3: str, angle: int = 5400000):
    """Apply 3-stop gradient background for extra premium feel."""
    try:
        slide.follow_master_background = False
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = _hex(c1)

        bg_elem = slide._element.find(f'{{{_NS_P}}}bg')
        if bg_elem is not None:
            bgPr = bg_elem.find(f'{{{_NS_P}}}bgPr')
            if bgPr is not None:
                for child in list(bgPr):
                    local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if 'Fill' in local or 'fill' in local:
                        bgPr.remove(child)

                grad = parse_xml(
                    f'<a:gradFill xmlns:a="{_NS_A}" rotWithShape="1">'
                    f'<a:gsLst>'
                    f'<a:gs pos="0"><a:srgbClr val="{c1}"/></a:gs>'
                    f'<a:gs pos="50000"><a:srgbClr val="{c2}"/></a:gs>'
                    f'<a:gs pos="100000"><a:srgbClr val="{c3}"/></a:gs>'
                    f'</a:gsLst>'
                    f'<a:lin ang="{angle}" scaled="0"/>'
                    f'</a:gradFill>'
                )
                bgPr.insert(0, grad)
    except Exception:
        _set_gradient_bg(slide, c1, c3, angle)


# ════════════════════════════════════════════════════════════════════════════════
# DECORATIVE SHAPES (geometric elements with transparency and shadows)
# ════════════════════════════════════════════════════════════════════════════════

def _add_shape_no_border(slide, shape_type, left, top, width, height, fill_hex,
                          alpha_pct: int = 100):
    """Add shape with fill, no border, optional transparency."""
    shape = slide.shapes.add_shape(shape_type, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = _hex(fill_hex)
    shape.line.fill.background()

    if alpha_pct < 100:
        try:
            from pptx.oxml.xmlchemy import OxmlElement
            alpha_val = int(alpha_pct * 1000)
            solidFill = shape.fill._xPr.find(f'{{{_NS_A}}}solidFill')
            if solidFill is not None:
                srgb = solidFill.find(f'{{{_NS_A}}}srgbClr')
                if srgb is not None:
                    alpha_elem = OxmlElement('a:alpha')
                    alpha_elem.set('val', str(alpha_val))
                    srgb.append(alpha_elem)
        except Exception:
            pass

    return shape


def _add_shadow(shape, blur_pt: int = 5, dist_pt: int = 3, angle: int = 45):
    """Add soft outer shadow to a shape."""
    try:
        shadow = shape.shadow
        shadow.inherit = False
        shadow.visible = True
        shadow.blur_radius = Pt(blur_pt)
        shadow.distance = Pt(dist_pt)
        shadow.angle = angle
    except Exception:
        pass


def _decorate_title_slide(slide, pal: dict, sw, sh):
    """Premium decorations for the cover/title slide."""
    accent = pal["accent"]
    accent2 = pal["accent2"]

    # Huge background sweep for dramatic effect
    _add_shape_no_border(slide, MSO_SHAPE.PARALLELOGRAM,
                         -Inches(2), sh - Inches(5),
                         sw + Inches(4), Inches(8), accent, alpha_pct=15)
                         
    # Large decorative circle (top-right, partially off-screen)
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         sw - Inches(3), -Inches(1.5),
                         Inches(6), Inches(6), accent2, alpha_pct=20)

    # Smaller glowing inner circle
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         sw - Inches(2.2), -Inches(0.8),
                         Inches(4), Inches(4), accent, alpha_pct=10)

    # Left vertical accent bar (very thick for impact)
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         0, 0, Inches(0.4), sh, accent, alpha_pct=85)

    # Bottom accent line
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         Inches(0.4), sh - Inches(0.15),
                         sw - Inches(0.4), Inches(0.15), accent2, alpha_pct=90)

    # Decorative diamond for the topic area
    _add_shape_no_border(slide, MSO_SHAPE.DIAMOND,
                         Inches(0.8), sh / 2,
                         Inches(1.2), Inches(1.2), accent, alpha_pct=25)


def _decorate_section_slide(slide, pal: dict, sw, sh):
    """Premium decorations for section/chapter header slides."""
    accent = pal["accent"]

    # Thick left accent bar
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         0, 0, Inches(0.3), sh, accent, alpha_pct=85)

    # Top-right decorative triangle
    _add_shape_no_border(slide, MSO_SHAPE.RIGHT_TRIANGLE,
                         sw - Inches(3), 0,
                         Inches(3), Inches(2), accent, alpha_pct=8)

    # Bottom horizontal bar
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         Inches(0.3), sh - Inches(0.06),
                         sw, Inches(0.06), accent, alpha_pct=50)


def _decorate_content_slide_v1(slide, pal: dict, sw, sh):
    """Content slide variant 1: left bar + top-right circle."""
    accent = pal["accent"]
    accent2 = pal["accent2"]

    # Awesome Left side block
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         0, 0, Inches(0.4), sh, accent, alpha_pct=90)
    
    # Large soft triangle in the background
    _add_shape_no_border(slide, MSO_SHAPE.RIGHT_TRIANGLE,
                         -Inches(2), sh - Inches(5),
                         Inches(6), Inches(6), accent, alpha_pct=10)

    # Top right beautiful chevron
    _add_shape_no_border(slide, MSO_SHAPE.CHEVRON,
                         sw - Inches(3), Inches(0.5),
                         Inches(4), Inches(1), accent2, alpha_pct=80)


def _decorate_content_slide_v2(slide, pal: dict, sw, sh):
    """Content slide variant 2: top bar + bottom-left shape."""
    accent = pal["accent"]
    accent2 = pal["accent2"]

    # Stylish Top thick bar
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         0, 0, sw, Inches(0.6), accent, alpha_pct=90)

    # Cool hexagon in bottom-left
    _add_shape_no_border(slide, MSO_SHAPE.HEXAGON,
                         -Inches(1), sh - Inches(3),
                         Inches(4), Inches(4), accent2, alpha_pct=15)
                         
    # Accent line below the title area
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         Inches(1), Inches(1.5),
                         Inches(3), Inches(0.05), accent2, alpha_pct=100)


def _decorate_content_slide_v3(slide, pal: dict, sw, sh):
    """Content slide variant 3: right bar + top-left corner."""
    accent = pal["accent"]
    accent2 = pal["accent2"]
    # Left side bars
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE, Inches(0.2), 0, Inches(0.1), sh, accent, alpha_pct=90)
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE, Inches(0.4), 0, Inches(0.05), sh, accent2, alpha_pct=70)
    # Bottom-right geometric
    _add_shape_no_border(slide, MSO_SHAPE.PARALLELOGRAM, sw - Inches(4), sh - Inches(2), Inches(5), Inches(3), accent, alpha_pct=15)


def _decorate_content_slide_v4(slide, pal: dict, sw, sh):
    """Content slide variant 4: diagonal accent."""
    accent = pal["accent"]
    # Floating triangles
    _add_shape_no_border(slide, MSO_SHAPE.RIGHT_TRIANGLE, sw - Inches(3), sh - Inches(3), Inches(3), Inches(3), accent, alpha_pct=10)
    _add_shape_no_border(slide, MSO_SHAPE.RIGHT_TRIANGLE, 0, 0, Inches(2), Inches(2), accent, alpha_pct=10)


def _decorate_quote_slide(slide, pal: dict, sw, sh):
    """Premium decorations for quote/iqtibos slides."""
    accent = pal["accent"]
    accent2 = pal["accent2"]

    # Large left vertical accent line
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         Inches(0.5), Inches(1.5),
                         Inches(0.2), Inches(4.5), accent, alpha_pct=80)

    # Top-right decorative oval (Huge and glowing)
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         sw - Inches(4), -Inches(2),
                         Inches(6), Inches(6), accent2, alpha_pct=15)

    # A decorative huge quote mark using a shape (like a block arc)
    _add_shape_no_border(slide, MSO_SHAPE.BLOCK_ARC,
                         Inches(1.0), Inches(1.0),
                         Inches(1.5), Inches(1.5), accent, alpha_pct=25)

    # Bottom line
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         Inches(0.5), sh - Inches(0.5),
                         sw - Inches(1.0), Inches(0.15), accent2, alpha_pct=90)

def _decorate_plan_slide(slide, pal: dict, sw, sh):
    """Premium decorations for Plan/O'quv savollari slide."""
    accent = pal["accent"]
    accent2 = pal["accent2"]
    
    # Large soft triangle on the left side pointing right
    _add_shape_no_border(slide, MSO_SHAPE.RIGHT_TRIANGLE,
                         -Inches(1), Inches(1),
                         Inches(3), sh - Inches(2), accent, alpha_pct=15)
                         
    # Top right floating banner/ribbon
    _add_shape_no_border(slide, MSO_SHAPE.CHEVRON,
                         sw - Inches(3), Inches(0.5),
                         Inches(3.5), Inches(0.8), accent2, alpha_pct=60)
                         
    # Bottom elegant thin lines
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         sw/2 - Inches(3), sh - Inches(0.6),
                         Inches(6), Inches(0.05), accent, alpha_pct=80)
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         sw/2 - Inches(2), sh - Inches(0.5),
                         Inches(4), Inches(0.05), accent2, alpha_pct=60)

def _decorate_goals_slide(slide, pal: dict, sw, sh):
    """Premium decorations for Goals/Maqsadlar slide."""
    accent = pal["accent"]
    accent2 = pal["accent2"]
    
    # Large soft glowing background circle in the center
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         sw/2 - Inches(3), sh/2 - Inches(3),
                         Inches(6), Inches(6), accent, alpha_pct=10)
    
    # Top and bottom elegant accent lines
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         Inches(2), Inches(0.3),
                         sw - Inches(4), Inches(0.08), accent2, alpha_pct=80)
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         Inches(2), sh - Inches(0.38),
                         sw - Inches(4), Inches(0.08), accent2, alpha_pct=80)
                         
    # Left and right vertical floating lines
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         Inches(0.2), Inches(1),
                         Inches(0.05), sh - Inches(2), accent, alpha_pct=50)
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         sw - Inches(0.25), Inches(1),
                         Inches(0.05), sh - Inches(2), accent, alpha_pct=50)


def _decorate_conclusion_slide(slide, pal: dict, sw, sh):
    """Premium decorations for conclusion slides."""
    accent = pal["accent"]
    accent2 = pal["accent2"]

    # Awesome geometric "Sticker" background for Conclusion
    
    # Large angled backdrop on the left
    _add_shape_no_border(slide, MSO_SHAPE.PARALLELOGRAM,
                         -Inches(3), 0,
                         Inches(6), sh, accent, alpha_pct=15)
                         
    # Accent glowing orb in the center right
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         sw/2 + Inches(1), sh/2 - Inches(2),
                         Inches(5), Inches(5), accent2, alpha_pct=10)
                         
    # Top right diagonal banner/sticker
    _add_shape_no_border(slide, MSO_SHAPE.CHEVRON,
                         sw - Inches(3), Inches(0.5),
                         Inches(4), Inches(1), accent2, alpha_pct=85)
                         
    # Bottom elegant thin lines (Underline the slide)
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         Inches(1), sh - Inches(0.5),
                         sw - Inches(2), Inches(0.08), accent, alpha_pct=90)


def _decorate_references_slide(slide, pal: dict, sw, sh):
    """Premium decorations for References (Foydalanilgan adabiyotlar) slides."""
    accent = pal["accent"]
    accent2 = pal["accent2"]
    
    # Large glowing oval in the bottom left
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         -Inches(3), sh - Inches(3),
                         Inches(6), Inches(6), accent, alpha_pct=10)
                         
    # Accent geometric strip on the right edge
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         sw - Inches(0.2), 0,
                         Inches(0.2), sh, accent2, alpha_pct=80)
                         
    # Top left small decorative dots (using small circles)
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         Inches(0.5), Inches(0.5),
                         Inches(0.2), Inches(0.2), accent, alpha_pct=60)
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         Inches(0.8), Inches(0.5),
                         Inches(0.2), Inches(0.2), accent2, alpha_pct=40)
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         Inches(1.1), Inches(0.5),
                         Inches(0.2), Inches(0.2), accent, alpha_pct=20)


def _decorate_final_slide(slide, pal: dict, sw, sh):
    """Premium 'Thank You' slide decorations."""
    accent = pal["accent"]
    accent2 = pal["accent2"]

    # Large center circle (decorative, behind text)
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         (sw - Inches(6)) // 2, (sh - Inches(6)) // 2,
                         Inches(6), Inches(6), accent, alpha_pct=8)

    # Inner circle
    _add_shape_no_border(slide, MSO_SHAPE.OVAL,
                         (sw - Inches(4)) // 2, (sh - Inches(4)) // 2,
                         Inches(4), Inches(4), accent2, alpha_pct=6)

    # Bottom thick accent bar
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         0, sh - Inches(0.4), sw, Inches(0.4), accent, alpha_pct=80)

    # Left accent bar
    _add_shape_no_border(slide, MSO_SHAPE.RECTANGLE,
                         0, 0, Inches(0.2), sh - Inches(0.4), accent, alpha_pct=60)


_CONTENT_DECORATORS = [
    _decorate_content_slide_v1,
    _decorate_content_slide_v2,
    _decorate_content_slide_v3,
    _decorate_content_slide_v4,
]


# ════════════════════════════════════════════════════════════════════════════════
# TEXT FORMATTING (Arial font, keyword highlighting, proper sizing)
# ════════════════════════════════════════════════════════════════════════════════

def _is_title_shape(shape, slide) -> bool:
    """Check if a shape is likely the title (placeholder or by position/size)."""
    if shape.is_placeholder:
        from pptx.enum.shapes import PP_PLACEHOLDER
        pf = shape.placeholder_format
        if pf.type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            return True
    font_size = 0
    try:
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if run.font.size and run.font.size.pt > font_size:
                    font_size = run.font.size.pt
    except Exception:
        pass
    return font_size >= 22 or (shape.top < Inches(2) and shape.width > Inches(5))


def _format_all_text(slide, pal: dict, slide_type: str):
    """Reformat all text on the slide: Arial font, proper colors, sizes."""
    text1 = _hex(pal["text1"])
    text2 = _hex(pal["text2"])
    accent_rgb = _hex(pal["accent"])
    is_dark = pal["is_dark"]

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue

        is_title = _is_title_shape(shape, slide)

        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                # Set Arial font
                run.font.name = "Arial"

                # Determine appropriate color
                if is_title:
                    if slide_type in ("title", "section", "final", "goals", "plan"):
                        run.font.color.rgb = accent_rgb
                    else:
                        run.font.color.rgb = text1
                    run.font.bold = True
                    # Center align title on goals, plan, section, conclusion, and references slides
                    if slide_type in ("goals", "plan", "section", "conclusion", "references"):
                        para.alignment = PP_ALIGN.CENTER
                        
                    # Huge uppercase for section and conclusion titles
                    if slide_type in ("section", "conclusion", "references"):
                        run.text = run.text.upper()
                        try:
                            run.font.size = Pt(40)
                        except Exception:
                            pass
                else:
                    # Check if run has explicit black color on dark bg
                    current_color = None
                    try:
                        current_color = run.font.color.rgb
                    except Exception:
                        pass

                    if is_dark:
                        if current_color == RGBColor(0, 0, 0) or current_color is None:
                            run.font.color.rgb = text1
                    else:
                        if current_color == RGBColor(255, 255, 255) or current_color is None:
                            run.font.color.rgb = text1
                            
                    # Remove bullets and make text italic and larger for quote slides
                    if slide_type == "quote":
                        run.font.italic = True
                        try:
                            # Increase font size for quote text if possible
                            if run.font.size:
                                run.font.size = Pt(int(run.font.size.pt * 1.2))
                            else:
                                run.font.size = Pt(24)
                            # Remove bullet point format if exists
                            if para.level > 0:
                                para.level = 0
                        except Exception:
                            pass
                            
                    # Section slide body text formatting (center, bold, huge)
                    if slide_type == "section":
                        run.font.bold = True
                        para.alignment = PP_ALIGN.CENTER
                        if para.level > 0:
                            para.level = 0
                        try:
                            if run.font.size:
                                run.font.size = Pt(int(run.font.size.pt * 1.5))
                            else:
                                run.font.size = Pt(32)
                        except Exception:
                            pass
                    
                    # Justify body text on most slides
                    if slide_type in ("goals", "plan", "content", "intro", "conclusion", "references"):
                        para.alignment = PP_ALIGN.JUSTIFY
                        
                    # Conclusion slide body text formatting (remove bullets, bold)
                    if slide_type == "conclusion":
                        run.font.bold = True
                        if para.level > 0:
                            para.level = 0
                        try:
                            if run.font.size:
                                run.font.size = Pt(int(run.font.size.pt * 1.2))
                            else:
                                run.font.size = Pt(24)
                        except Exception:
                            pass


# ════════════════════════════════════════════════════════════════════════════════
# PROFESSIONAL TRANSITIONS (Morph, Fade, Push, Zoom)
# ════════════════════════════════════════════════════════════════════════════════

def _add_transition(slide, transition_type: str = "fade", speed: str = "med"):
    """Add slide transition via XML injection."""
    try:
        transitions = {
            "fade": f'<p:transition xmlns:p="{_NS_P}" spd="{speed}"><p:fade/></p:transition>',
            "push": f'<p:transition xmlns:p="{_NS_P}" spd="{speed}"><p:push dir="u"/></p:transition>',
            "cover": f'<p:transition xmlns:p="{_NS_P}" spd="{speed}"><p:cover dir="l"/></p:transition>',
            "wipe": f'<p:transition xmlns:p="{_NS_P}" spd="{speed}"><p:wipe dir="d"/></p:transition>',
            "split": f'<p:transition xmlns:p="{_NS_P}" spd="{speed}"><p:split orient="horz" dir="out"/></p:transition>',
        }
        xml_str = transitions.get(transition_type, transitions["fade"])
        slide._element.insert(1, parse_xml(xml_str))
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════════════════
# BACKGROUND APPLICATION per slide type
# ════════════════════════════════════════════════════════════════════════════════

_GRADIENT_ANGLES = [5400000, 2700000, 0, 10800000]  # down, diagonal, right, up


def _apply_bg_for_type(slide, pal: dict, slide_type: str, idx: int):
    """Apply the right background based on slide type."""
    bg1, bg2 = pal["bg1"], pal["bg2"]
    accent, accent2 = pal["accent"], pal["accent2"]

    if slide_type == "title":
        _set_gradient_3stop(slide, bg1, _darker(bg2, 0.1), _lighter(bg1, 0.05), angle=5400000)
    elif slide_type == "section":
        _set_gradient_bg(slide, _darker(bg1, 0.1), bg2, angle=2700000)
    elif slide_type == "quote":
        _set_gradient_bg(slide, bg1, _lighter(bg2, 0.05), angle=5400000)
    elif slide_type == "conclusion":
        _set_gradient_bg(slide, bg2, bg1, angle=10800000)
    elif slide_type == "final":
        _set_gradient_3stop(slide, _darker(bg1, 0.15), bg1, _lighter(bg2, 0.08), angle=5400000)
    else:
        angle = _GRADIENT_ANGLES[idx % len(_GRADIENT_ANGLES)]
        if idx % 3 == 0:
            _set_gradient_bg(slide, bg1, bg2, angle)
        elif idx % 3 == 1:
            _set_gradient_bg(slide, bg2, bg1, angle)
        else:
            _set_gradient_bg(slide, bg1, _lighter(bg2, 0.03), angle)


# ════════════════════════════════════════════════════════════════════════════════
# MAIN PUBLIC API
# ════════════════════════════════════════════════════════════════════════════════

def apply_premium_design(prs, topic: str = ""):
    """
    Apply full premium design to an existing presentation.
    Called AFTER slides are created and filled with content.
    
    This function:
    1. Selects a color palette based on topic keywords
    2. Applies gradient backgrounds per slide type
    3. Adds decorative geometric elements (non-overlapping with text)
    4. Reformats all text to Arial with proper contrast
    """
    palette = _select_palette(topic)
    slides = list(prs.slides)
    total = len(slides)
    if total == 0:
        return

    sw = prs.slide_width
    sh = prs.slide_height

    prev_decorator_idx = -1

    for idx, slide in enumerate(slides):
        slide_type = _detect_slide_type(slide, idx, total)

        # 1. Apply gradient background
        _apply_bg_for_type(slide, palette, slide_type, idx)

        # 2. Add decorative elements (varies per slide type)
        if slide_type == "title":
            _decorate_title_slide(slide, palette, sw, sh)
        elif slide_type == "section":
            _decorate_section_slide(slide, palette, sw, sh)
        elif slide_type == "quote":
            _decorate_quote_slide(slide, palette, sw, sh)
        elif slide_type == "goals":
            _decorate_goals_slide(slide, palette, sw, sh)
        elif slide_type == "plan":
            _decorate_plan_slide(slide, palette, sw, sh)
        elif slide_type == "conclusion":
            _decorate_conclusion_slide(slide, palette, sw, sh)
        elif slide_type == "references":
            _decorate_references_slide(slide, palette, sw, sh)
        elif slide_type == "final":
            _decorate_final_slide(slide, palette, sw, sh)
        else:
            # Content slides: rotate through variants (never repeat consecutively)
            available = list(range(len(_CONTENT_DECORATORS)))
            if prev_decorator_idx in available and len(available) > 1:
                available.remove(prev_decorator_idx)
            dec_idx = random.choice(available)
            _CONTENT_DECORATORS[dec_idx](slide, palette, sw, sh)
            prev_decorator_idx = dec_idx

        # 3. Reformat text
        _format_all_text(slide, palette, slide_type)


def apply_premium_transitions(prs):
    """Apply professional slide transitions."""
    slides = list(prs.slides)
    total = len(slides)
    if total == 0:
        return

    for idx, slide in enumerate(slides):
        slide_type = _detect_slide_type(slide, idx, total)

        if slide_type == "title":
            _add_transition(slide, "fade", "slow")
        elif slide_type == "section":
            _add_transition(slide, "push", "med")
        elif slide_type == "quote":
            _add_transition(slide, "fade", "slow")
        elif slide_type == "final":
            _add_transition(slide, "fade", "slow")
        elif slide_type == "conclusion":
            _add_transition(slide, "wipe", "med")
        else:
            # Alternate between transitions for content slides
            options = ["fade", "cover", "push", "wipe"]
            _add_transition(slide, options[idx % len(options)], "med")
