"""
Generates clean, on-brand clothing-silhouette placeholder images locally
with Pillow — no internet, no third-party photo APIs, so there is zero
chance of an unrelated photo (an animal, a random object, a visible face)
ever ending up in the seeded catalog. Every image is a simple flat-lay
style garment icon in the product's own color.

This file is intentionally prefixed with an underscore so Django's
management-command loader ignores it — it's a plain helper module, not a
command.
"""
import random
from io import BytesIO

from PIL import Image, ImageDraw, ImageFilter
from django.core.files.base import ContentFile

BG = (240, 233, 223)        # site "sand" tone
INK = (26, 21, 18)
GOLD = (184, 146, 90)


def hex_to_rgb(hex_code):
    hex_code = (hex_code or '#8a6d4a').lstrip('#')
    if len(hex_code) != 6:
        hex_code = '8a6d4a'
    return tuple(int(hex_code[i:i + 2], 16) for i in (0, 2, 4))


def _lighten(color, amt=0.25):
    r, g, b = color
    return (int(r + (255 - r) * amt), int(g + (255 - g) * amt), int(b + (255 - b) * amt))


def _darken(color, amt=0.22):
    r, g, b = color
    return (int(r * (1 - amt)), int(g * (1 - amt)), int(b * (1 - amt)))


def _mirror(pts):
    return [(1 - x, y) for x, y in pts]


def _tunic(hem=0.85, variant='front'):
    pts = [
        (0.42, 0.10), (0.58, 0.10),
        (0.72, 0.17), (0.80, 0.30),
        (0.68, 0.33), (0.61, 0.23),
        (0.61, hem), (0.39, hem),
        (0.39, 0.23), (0.32, 0.33),
        (0.20, 0.30), (0.28, 0.17),
    ]
    return _mirror(pts) if variant == 'back' else pts


def _robe(variant='front'):
    pts = [
        (0.44, 0.08), (0.56, 0.08),
        (0.66, 0.14), (0.76, 0.26),
        (0.66, 0.30), (0.59, 0.20),
        (0.64, 0.92), (0.36, 0.92),
        (0.41, 0.20), (0.34, 0.30),
        (0.24, 0.26), (0.34, 0.14),
    ]
    return _mirror(pts) if variant == 'back' else pts


def _dress(variant='front'):
    pts = [
        (0.43, 0.10), (0.57, 0.10),
        (0.66, 0.17), (0.60, 0.28),
        (0.68, 0.55), (0.78, 0.85), (0.22, 0.85), (0.32, 0.55),
        (0.40, 0.28), (0.34, 0.17),
    ]
    return _mirror(pts) if variant == 'back' else pts


def _croptop(variant='front'):
    pts = [
        (0.42, 0.18), (0.58, 0.18),
        (0.70, 0.24), (0.62, 0.35),
        (0.64, 0.60), (0.36, 0.60),
        (0.38, 0.35), (0.30, 0.24),
    ]
    return _mirror(pts) if variant == 'back' else pts


def _trousers(variant='front'):
    pts = [
        (0.35, 0.12), (0.65, 0.12), (0.65, 0.48), (0.72, 0.86), (0.58, 0.86),
        (0.52, 0.50), (0.48, 0.50), (0.42, 0.86), (0.28, 0.86), (0.35, 0.48),
    ]
    return _mirror(pts) if variant == 'back' else pts


SHAPE_FUNCS = {
    'kameez': lambda v: _tunic(0.85, v),
    'kurti': lambda v: _tunic(0.60, v),
    'suit': lambda v: _tunic(0.75, v),
    'abaya': lambda v: _robe(v),
    'dress': lambda v: _dress(v),
    'top': lambda v: _croptop(v),
    'trousers': lambda v: _trousers(v),
    'kids_boy': lambda v: _tunic(0.55, v),
    'kids_girl': lambda v: _dress(v),
    'kids_set': lambda v: _tunic(0.55, v),
}


def garment_image(shape, color_hex, w=800, h=1000, variant='front', seed=0):
    """A single stylized flat-lay clothing icon — guaranteed to depict only
    a garment silhouette in the product's own color, nothing else."""
    img = Image.new('RGB', (w, h), BG)
    draw = ImageDraw.Draw(img)
    draw.ellipse([w * 0.05, h * 0.03, w * 0.95, h * 0.99], fill=_lighten(BG, 0.4))

    color = hex_to_rgb(color_hex)
    pts_norm = SHAPE_FUNCS.get(shape, SHAPE_FUNCS['kameez'])(variant)
    abs_pts = [(x * w, y * h) for x, y in pts_norm]
    draw.polygon(abs_pts, fill=color, outline=_darken(color, 0.3), width=3)

    # subtle scattered texture confined to the garment silhouette via a mask
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).polygon(abs_pts, fill=255)
    pattern = Image.new('RGB', (w, h), color)
    pdraw = ImageDraw.Draw(pattern)
    rnd = random.Random(seed)
    accent = _lighten(color, 0.55)
    minx, miny = min(p[0] for p in abs_pts), min(p[1] for p in abs_pts)
    maxx, maxy = max(p[0] for p in abs_pts), max(p[1] for p in abs_pts)
    dot_count = max(20, int((maxx - minx) * (maxy - miny) / 1800))
    for _ in range(dot_count):
        px, py = rnd.uniform(minx, maxx), rnd.uniform(miny, maxy)
        r = rnd.uniform(2.5, 5.5)
        pdraw.ellipse([px - r, py - r, px + r, py + r], fill=accent)
    img.paste(pattern, (0, 0), mask)

    if variant == 'front':
        draw.line([abs_pts[0], abs_pts[1]], fill=_darken(color, 0.4), width=4)

    return img.filter(ImageFilter.SMOOTH_MORE)


def hero_banner_image(w=1600, h=900, seed=0):
    """A moody ink-to-gold gradient banner with faint garment silhouettes —
    evokes a boutique clothing store without depicting any specific photo,
    face, or unrelated subject."""
    img = Image.new('RGB', (w, h), INK)
    draw = ImageDraw.Draw(img)
    bottom = (58, 42, 26)
    for y in range(h):
        t = y / h
        r = int(INK[0] + (bottom[0] - INK[0]) * t)
        g = int(INK[1] + (bottom[1] - INK[1]) * t)
        b = int(INK[2] + (bottom[2] - INK[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    img = img.convert('RGBA')
    shapes = ['kameez', 'abaya', 'dress']
    for i, shape in enumerate(shapes):
        pts_norm = SHAPE_FUNCS[shape]('front')
        gw, gh = w * 0.30, h * 0.80
        offset_x = w * (0.08 + i * 0.32)
        offset_y = h * 0.10
        abs_pts = [(offset_x + x * gw, offset_y + y * gh) for x, y in pts_norm]
        overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(overlay).polygon(abs_pts, fill=GOLD + (36,))
        img = Image.alpha_composite(img, overlay)

    return img.convert('RGB')


def to_content_file(img, filename):
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=88)
    return filename, ContentFile(buf.getvalue())
