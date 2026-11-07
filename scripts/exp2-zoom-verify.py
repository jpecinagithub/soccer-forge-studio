#!/usr/bin/env python3
"""Zoom verification sheets for flagged B1 reference positions (exp2).

For each flagged t_abs: 240x240 crop at ORIGINAL resolution centred on the
1C position, upscaled 3x (720x720), red crosshair at centre (= 1C position),
plus a 40-px grid (in original px) so offsets can be read off.
4 crops per sheet (2x2). Output: data/clips/work/exp2/b1-zoom/zoom-01..07.jpg
and b1-zoom/crops.csv with crop origins.
"""
import csv
import os
import subprocess
import sys

CLIP = "data/clips/georgia-espana-rfef.mp4"
CORR = "data/clips/work/exp2/b1-verify-corrections.csv"
REF = "data/clips/work/exp1c/ref-positions.csv"
OUT = "data/clips/work/exp2/b1-zoom"
SIZE = 240          # crop side in original px
SCALE = 3           # upscale factor
CELL = SIZE * SCALE  # 720

os.makedirs(OUT, exist_ok=True)

flags = []
with open(CORR) as fh:
    for r in csv.DictReader(fh):
        if r["verdict"] == "flag-zoom":
            flags.append((float(r["t_abs"]), r["segment"], float(r["x_1c"]), float(r["y_1c"])))
flags.sort()
print(f"{len(flags)} flagged positions")

# Extract one full frame per flagged time (ffmpeg, exact seek)
frames = {}
for i, (t, seg, x, y) in enumerate(flags):
    fp = os.path.join(OUT, f"frame-{t:06.1f}.png")
    if not os.path.exists(fp):
        subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", f"{t:.1f}", "-i", CLIP,
             "-frames:v", "1", "-y", fp], check=True)
    frames[t] = fp

# Build crops with PIL: crop 240x240 centred on (x,y), upscale 3x (NEAREST
# keeps pixel edges crisp), draw crosshair + 40px grid + label.
from PIL import Image, ImageDraw, ImageFont

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    font_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
except Exception:
    font = ImageFont.load_default()
    font_s = font

crops_meta = []
for i, (t, seg, x, y) in enumerate(flags):
    im = Image.open(frames[t]).convert("RGB")
    ox = int(round(x)) - SIZE // 2
    oy = int(round(y)) - SIZE // 2
    ox = max(0, min(1920 - SIZE, ox))
    oy = max(0, min(1080 - SIZE, oy))
    crop = im.crop((ox, oy, ox + SIZE, oy + SIZE)).resize(
        (CELL, CELL), Image.NEAREST)
    d = ImageDraw.Draw(crop)
    # grid every 40 orig px = 120 display px
    for g in range(40, SIZE, 40):
        gp = g * SCALE
        d.line([(gp, 0), (gp, CELL)], fill=(255, 255, 0), width=1)
        d.line([(0, gp), (CELL, gp)], fill=(255, 255, 0), width=1)
    # crosshair at centre (1C position)
    cx = cy = CELL // 2
    d.line([(cx - 30, cy), (cx + 30, cy)], fill=(255, 0, 0), width=3)
    d.line([(cx, cy - 30), (cx, cy + 30)], fill=(255, 0, 0), width=3)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], outline=(255, 0, 0), width=3)
    d.rectangle([0, 0, CELL - 1, 44], fill=(0, 0, 0))
    d.text((8, 8), f"{t:.1f}s {seg}  1C=({int(x)},{int(y)})", fill=(255, 255, 0), font=font)
    crops_meta.append((t, seg, x, y, ox, oy, crop))

with open(os.path.join(OUT, "crops.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["t_abs", "segment", "x_1c", "y_1c", "ox", "oy"])
    for t, seg, x, y, ox, oy, _ in crops_meta:
        w.writerow([f"{t:.1f}", seg, int(x), int(y), ox, oy])

# 2x2 sheets
for si in range(0, len(crops_meta), 4):
    group = crops_meta[si:si + 4]
    sheet = Image.new("RGB", (CELL * 2, CELL * 2), (0, 0, 0))
    for j, (_, _, _, _, _, _, crop) in enumerate(group):
        sheet.paste(crop, ((j % 2) * CELL, (j // 2) * CELL))
    sheet.save(os.path.join(OUT, f"zoom-{si // 4 + 1:02d}.jpg"), quality=90)
    print(f"zoom-{si // 4 + 1:02d}.jpg: {[f'{g[0]:.1f}' for g in group]}")
print("done")
