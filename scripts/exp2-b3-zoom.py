#!/usr/bin/env python3
"""Zoom/wide verification sheets genéricos para la referencia B3 (exp2).

Para cada fila (t_abs, segment, x, y) de un CSV de entrada: recorte
SIZE x SIZE a RESOLUCIÓN ORIGINAL centrado en (x, y), ampliado SCALE x,
cruz roja en el centro (= posición de entrada) y rejilla cada 40 px
originales para leer desplazamientos. 4 recortes por hoja (2x2).

Uso (zoom 3x sobre propuestas YOLO):
    python3 scripts/exp2-b3-zoom.py --in data/clips/work/exp2/b3-proposals.csv \
        --clip data/clips/espana-bulgaria-rfef.mp4 --size 240 --scale 3 \
        --out data/clips/work/exp2/b3-zoom
Uso (ancho 2x sobre posiciones interpoladas):
    python3 scripts/exp2-b3-zoom.py --in data/clips/work/exp2/b3-interp.csv \
        --clip data/clips/espana-bulgaria-rfef.mp4 --size 480 --scale 2 \
        --out data/clips/work/exp2/b3-wide
Entrada CSV: columnas t_abs,segment,x,y
Salida: <out>/zoom-01..N.jpg (u wide-01..N.jpg según --tag) y <out>/crops.csv
"""

import argparse
import csv
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--size", type=int, default=240)
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="zoom")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    rows = []
    with open(args.inp, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append((float(r["t_abs"]), r["segment"],
                         float(r["x"]), float(r["y"])))
    rows.sort()
    print(f"{len(rows)} posiciones")
    size, scale = args.size, args.scale
    cell = size * scale

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except Exception:
        font = ImageFont.load_default()

    frames = {}
    for (t, seg, x, y) in rows:
        fp = os.path.join(args.out, f"frame-{t:06.1f}.png")
        if not os.path.exists(fp):
            subprocess.run(
                ["ffmpeg", "-v", "error", "-ss", f"{t:.1f}", "-i", args.clip,
                 "-frames:v", "1", "-y", fp], check=True)
        frames[t] = fp

    crops_meta = []
    for (t, seg, x, y) in rows:
        im = Image.open(frames[t]).convert("RGB")
        ox = int(round(x)) - size // 2
        oy = int(round(y)) - size // 2
        ox = max(0, min(1920 - size, ox))
        oy = max(0, min(1080 - size, oy))
        crop = im.crop((ox, oy, ox + size, oy + size)).resize(
            (cell, cell), Image.NEAREST)
        d = ImageDraw.Draw(crop)
        for g in range(40, size, 40):
            gp = g * scale
            d.line([(gp, 0), (gp, cell)], fill=(255, 255, 0), width=1)
            d.line([(0, gp), (cell, gp)], fill=(255, 255, 0), width=1)
        cx = cy = cell // 2
        d.line([(cx - 30, cy), (cx + 30, cy)], fill=(255, 0, 0), width=3)
        d.line([(cx, cy - 30), (cx, cy + 30)], fill=(255, 0, 0), width=3)
        d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12],
                  outline=(255, 0, 0), width=3)
        d.rectangle([0, 0, cell - 1, 44], fill=(0, 0, 0))
        d.text((8, 8), f"{t:.1f}s {seg}  ({int(x)},{int(y)})",
               fill=(255, 255, 0), font=font)
        crops_meta.append((t, seg, x, y, ox, oy, crop))

    with open(os.path.join(args.out, "crops.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["t_abs", "segment", "x", "y", "ox", "oy"])
        for t, seg, x, y, ox, oy, _ in crops_meta:
            w.writerow([f"{t:.1f}", seg, int(x), int(y), ox, oy])

    for si in range(0, len(crops_meta), 4):
        group = crops_meta[si:si + 4]
        sheet = Image.new("RGB", (cell * 2, cell * 2), (0, 0, 0))
        for j, (_, _, _, _, _, _, crop) in enumerate(group):
            sheet.paste(crop, ((j % 2) * cell, (j // 2) * cell))
        sheet.save(os.path.join(args.out, f"{args.tag}-{si // 4 + 1:02d}.jpg"),
                   quality=90)
        print(f"{args.tag}-{si // 4 + 1:02d}.jpg: "
              f"{[f'{g[0]:.1f}' for g in group]}")
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
