#!/usr/bin/env python3
"""Confirmation 3x zooms centred on CORRECTED positions (not 1C) for the
ambiguous S2b frames, to confirm the ball is really there (vs a sock).
240x240 crop at original res, 3x upscale, crosshair at centre (= corrected
position). Output: data/clips/work/exp2/b1-confirm/confirm-01.jpg + csv.
"""
import csv
import os

from PIL import Image, ImageDraw, ImageFont

ZOOM = "data/clips/work/exp2/b1-zoom"   # full frames already extracted
OUT = "data/clips/work/exp2/b1-confirm"
SIZE = 240
SCALE = 3
CELL = SIZE * SCALE

# (t_abs, segment, x_corr, y_corr)
CASES = [
    (138.8, "s2b", 1381, 575),
    (139.6, "s2b", 1547, 577),
    (140.4, "s2b", 1372, 711),
    (141.6, "s2b", 1346, 572),
]

os.makedirs(OUT, exist_ok=True)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
except Exception:
    font = ImageFont.load_default()

meta = []
for t, seg, x, y in CASES:
    fp = os.path.join(ZOOM, f"frame-{t:06.1f}.png")
    im = Image.open(fp).convert("RGB")
    ox = int(x) - SIZE // 2
    oy = int(y) - SIZE // 2
    ox = max(0, min(1920 - SIZE, ox))
    oy = max(0, min(1080 - SIZE, oy))
    crop = im.crop((ox, oy, ox + SIZE, oy + SIZE)).resize((CELL, CELL), Image.NEAREST)
    d = ImageDraw.Draw(crop)
    for g in range(40, SIZE, 40):
        gp = g * SCALE
        d.line([(gp, 0), (gp, CELL)], fill=(255, 255, 0), width=1)
        d.line([(0, gp), (CELL, gp)], fill=(255, 255, 0), width=1)
    cx = cy = CELL // 2
    d.line([(cx - 30, cy), (cx + 30, cy)], fill=(255, 0, 0), width=3)
    d.line([(cx, cy - 30), (cx, cy + 30)], fill=(255, 0, 0), width=3)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], outline=(255, 0, 0), width=3)
    d.rectangle([0, 0, CELL - 1, 44], fill=(0, 0, 0))
    d.text((8, 8), f"{t:.1f}s {seg}  CORR=({x},{y})", fill=(255, 255, 0), font=font)
    meta.append((t, seg, x, y, ox, oy, crop))

sheet = Image.new("RGB", (CELL * 2, CELL * 2), (0, 0, 0))
for j, (_, _, _, _, _, _, crop) in enumerate(meta):
    sheet.paste(crop, ((j % 2) * CELL, (j // 2) * CELL))
sheet.save(os.path.join(OUT, "confirm-01.jpg"), quality=90)
with open(os.path.join(OUT, "confirm-crops.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["t_abs", "segment", "x_corr", "y_corr", "ox", "oy"])
    for t, seg, x, y, ox, oy, _ in meta:
        w.writerow([f"{t:.1f}", seg, x, y, ox, oy])
print("done", [f"{m[0]:.1f}" for m in meta])
