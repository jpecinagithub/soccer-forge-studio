#!/usr/bin/env python3
"""Experimento 2 — Hojas de verificación de la referencia a resolución original.

Para cada posición V de la referencia 1C (data/clips/work/exp1c/ref-positions.csv),
extrae el fotograma del clip B1 original, recorta 480x480 a resolución original
centrado en la posición anotada (con clamp a los bordes), dibuja una cruz en la
posición anotada y compone hojas de 12 recortes (4x3) para revisión visual.

La posición final se determina sobre el recorte a resolución original, nunca
sobre el fotograma reducido: la lección de 1C es que las celdas de 960x540
introdujeron errores de ~40-80 px.

Uso:
    python3 scripts/exp2-verify-ref.py
Salida:
    data/clips/work/exp2/b1-verify/sheet-NN.jpg
    data/clips/work/exp2/b1-verify/crops.csv  (t_abs, segment, x, y, ox, oy)
"""

import csv
import os
import subprocess

from PIL import Image, ImageDraw

CLIP = "data/clips/georgia-espana-rfef.mp4"
REF = "data/clips/work/exp1c/ref-positions.csv"
OUTDIR = "data/clips/work/exp2/b1-verify"
CROP = 480
COLS, ROWS = 4, 3
PER_SHEET = COLS * ROWS


def extract_frame(t_abs: float, out: str) -> None:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t_abs:.2f}", "-i", CLIP,
         "-frames:v", "1", "-f", "image2", "-c", "png", out],
        check=True,
    )


def main() -> int:
    os.makedirs(OUTDIR, exist_ok=True)
    rows = []
    with open(REF, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["status"] == "V":
                rows.append(r)
    print(f"{len(rows)} posiciones V a verificar")

    crops = []
    for i, r in enumerate(rows):
        t = float(r["t_abs"])
        x, y = int(r["x"]), int(r["y"])
        frame_png = f"/tmp/exp2-verify-f{i:03d}.png"
        extract_frame(t, frame_png)
        im = Image.open(frame_png).convert("RGB")
        W, H = im.size
        ox = min(max(x - CROP // 2, 0), W - CROP)
        oy = min(max(y - CROP // 2, 0), H - CROP)
        crop = im.crop((ox, oy, ox + CROP, oy + CROP))
        d = ImageDraw.Draw(crop)
        cx, cy = x - ox, y - oy
        # cruz en la posición anotada
        d.line([(cx - 20, cy), (cx + 20, cy)], fill=(255, 0, 0), width=3)
        d.line([(cx, cy - 20), (cx, cy + 20)], fill=(255, 0, 0), width=3)
        d.ellipse([(cx - 12, cy - 12), (cx + 12, cy + 12)],
                  outline=(255, 0, 0), width=2)
        # etiqueta de tiempo
        d.rectangle([(0, 0), (110, 26)], fill=(0, 0, 0))
        d.text((4, 6), f"{t:.1f}s {r['segment']}", fill=(255, 255, 0))
        crops.append((crop, r, ox, oy))
        os.remove(frame_png)

    with open(os.path.join(OUTDIR, "crops.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["t_abs", "segment", "x", "y", "ox", "oy"])
        for crop, r, ox, oy in crops:
            w.writerow([r["t_abs"], r["segment"], r["x"], r["y"], ox, oy])

    for s in range((len(crops) + PER_SHEET - 1) // PER_SHEET):
        chunk = crops[s * PER_SHEET:(s + 1) * PER_SHEET]
        sheet = Image.new("RGB", (COLS * CROP, ROWS * CROP), "white")
        for j, (crop, r, ox, oy) in enumerate(chunk):
            sheet.paste(crop, ((j % COLS) * CROP, (j // COLS) * CROP))
        path = os.path.join(OUTDIR, f"sheet-{s + 1:02d}.jpg")
        sheet.save(path, quality=92)
        print(path, len(chunk), "recortes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
