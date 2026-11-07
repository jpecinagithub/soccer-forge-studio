#!/usr/bin/env python3
"""Wider verification crops (480x480 at original res, 2x upscale) for the
flagged B1 positions where the ball was NOT visible in the 240x240 zoom.
Uses the full frames already extracted in b1-zoom/frame-*.png.
Output: data/clips/work/exp2/b1-wide/wide-01..05.jpg + wide-crops.csv
"""
import csv
import os

from PIL import Image, ImageDraw, ImageFont

ZOOM = "data/clips/work/exp2/b1-zoom"
OUT = "data/clips/work/exp2/b1-wide"
SIZE = 480
SCALE = 2
CELL = SIZE * SCALE  # 960

WIDE_LIST = [138.8, 139.6, 140.4, 141.2, 141.6, 170.8,
             198.6, 199.0, 199.2, 200.0, 200.4, 200.6, 200.8,
             201.0, 201.2, 201.4, 201.6]

os.makedirs(OUT, exist_ok=True)

ref = {}
with open("data/clips/work/exp1c/ref-positions.csv") as fh:
    for r in csv.DictReader(fh):
        if r["x"] and r["y"]:
            ref[float(r["t_abs"])] = (r["segment"], float(r["x"]), float(r["y"]))

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
except Exception:
    font = ImageFont.load_default()

meta = []
for t in WIDE_LIST:
    seg, x, y = ref[t]
    fp = os.path.join(ZOOM, f"frame-{t:06.1f}.png")
    im = Image.open(fp).convert("RGB")
    ox = int(round(x)) - SIZE // 2
    oy = int(round(y)) - SIZE // 2
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
    d.text((8, 8), f"{t:.1f}s {seg}  1C=({int(x)},{int(y)})", fill=(255, 255, 0), font=font)
    meta.append((t, seg, x, y, ox, oy, crop))

with open(os.path.join(OUT, "wide-crops.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["t_abs", "segment", "x_1c", "y_1c", "ox", "oy"])
    for t, seg, x, y, ox, oy, _ in meta:
        w.writerow([f"{t:.1f}", seg, int(x), int(y), ox, oy])

for si in range(0, len(meta), 4):
    group = meta[si:si + 4]
    sheet = Image.new("RGB", (CELL * 2, CELL * 2), (0, 0, 0))
    for j, (_, _, _, _, _, _, crop) in enumerate(group):
        sheet.paste(crop, ((j % 2) * CELL, (j // 2) * CELL))
    sheet.save(os.path.join(OUT, f"wide-{si // 4 + 1:02d}.jpg"), quality=90)
    print(f"wide-{si // 4 + 1:02d}.jpg: {[f'{g[0]:.1f}' for g in group]}")
print("done")
