#!/usr/bin/env python3
"""Hojas de fotograma completo (960x540) para fotogramas B3 pendientes (exp2).

Para cada fila (t_abs, segment) de un CSV: extrae el fotograma completo a
resolución original, lo reduce a 960x540 y lo monta en hojas 2x2 con su
etiqueta de tiempo. Sirve para decidir si el balón está en el fotograma
(V candidato, con posición aproximada) o no (O: grada, vallas, primer
plano sin balón), antes de verificar con zoom 3x.

Uso:
    python3 scripts/exp2-b3-full.py --in data/clips/work/exp2/b3-pending.csv \
        --clip data/clips/espana-bulgaria-rfef.mp4 --out data/clips/work/exp2/b3-full
Entrada CSV: columnas t_abs,segment
Salida: <out>/full-01..N.jpg (2x2, 960x540 cada uno)
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
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    rows = []
    with open(args.inp, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append((float(r["t_abs"]), r["segment"]))
    rows.sort()
    print(f"{len(rows)} fotogramas")

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except Exception:
        font = ImageFont.load_default()

    frames = []
    for (t, seg) in rows:
        fp = os.path.join(args.out, f"frame-{t:06.1f}.png")
        if not os.path.exists(fp):
            subprocess.run(
                ["ffmpeg", "-v", "error", "-ss", f"{t:.1f}", "-i", args.clip,
                 "-frames:v", "1", "-y", fp], check=True)
        im = Image.open(fp).convert("RGB").resize((960, 540))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 200, 30], fill=(0, 0, 0))
        d.text((6, 4), f"{t:.1f}s {seg}", fill=(255, 255, 0), font=font)
        frames.append(((t, seg), im))

    for si in range(0, len(frames), 4):
        group = frames[si:si + 4]
        sheet = Image.new("RGB", (2 * 960, 2 * 540), (0, 0, 0))
        for j, ((t, seg), im) in enumerate(group):
            sheet.paste(im, ((j % 2) * 960, (j // 2) * 540))
        sheet.save(os.path.join(args.out, f"full-{si // 4 + 1:02d}.jpg"),
                   quality=90)
        print(f"full-{si // 4 + 1:02d}.jpg: {[f'{g[0][0]:.1f}' for g in group]}")
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
