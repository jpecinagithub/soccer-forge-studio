#!/usr/bin/env python3
"""Hojas limpias para la referencia temporal de posición del balón (Experimento 1C).

Construye hojas de contacto SIN cajas dibujadas (etiquetado ciego: la
referencia de posición no debe contaminarse con las detecciones) con
los fotogramas a 5 fps de los subtramos continuos de 1B:
  S1  70.0-77.8  (f01-f40)
  S2b 134.6-141.8 (f04-f40)  (corte entre 134.4 y 134.6)
  S3b 164.8-171.4 (f05-f38)  (corte entre 164.6 y 164.8; a primer plano ~171.5)
  S4  194.0-201.8 (f01-f40)

6 fotogramas por hoja (3x2, celdas 960x540 de un original 1920x1080).
Cada celda lleva su t_abs. Salida: data/clips/work/exp1c/sheets/.

Uso:
    python scripts/exp1c-sheets.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

LABELS_DIR = "data/clips/work/exp1b/labels"
OUT_DIR = "data/clips/work/exp1c/sheets"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

SEGMENTS = [
    ("s1", 70.0, 1, 40),
    ("s2", 134.0, 4, 40),
    ("s3", 164.0, 5, 38),
    ("s4", 194.0, 1, 40),
]

CELL_W, CELL_H, BAR = 960, 540, 44


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    items = []  # (segment, t_abs, frame_file)
    for seg, t0, k0, k1 in SEGMENTS:
        for k in range(k0, k1 + 1):
            t = round(t0 + (k - 1) * 0.2, 1)
            items.append((seg, t, os.path.join(LABELS_DIR, f"{seg}-f{k:02d}.jpg")))
    print(f"Fotogramas de referencia: {len(items)}")

    font = ImageFont.truetype(FONT, 30)
    n = 0
    for idx in range(0, len(items), 6):
        chunk = items[idx:idx + 6]
        sheet = Image.new("RGB", (CELL_W * 3, (CELL_H + BAR) * 2), "black")
        d = ImageDraw.Draw(sheet)
        for j, (seg, t, fn) in enumerate(chunk):
            img = Image.open(fn).convert("RGB")
            assert img.size == (1920, 1080), (fn, img.size)
            img = img.resize((CELL_W, CELL_H))
            x, y = (j % 3) * CELL_W, (j // 3) * (CELL_H + BAR)
            d.rectangle([x, y, x + CELL_W, y + BAR], fill=(20, 20, 20))
            d.text((x + 10, y + 6), f"t={t:.1f}s  ({seg})",
                   fill=(255, 255, 0), font=font)
            sheet.paste(img, (x, y + BAR))
        n += 1
        out = os.path.join(OUT_DIR, f"sheet-{n:02d}.jpg")
        sheet.save(out, quality=90)
        print(out, len(chunk), "frames:",
              ", ".join(f"{s}:{t:.1f}" for s, t, _ in chunk))
    print(f"Hojas: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
