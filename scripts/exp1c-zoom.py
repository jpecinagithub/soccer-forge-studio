#!/usr/bin/env python3
"""Experimento 1C: recortes ampliados (x2) de los fotogramas en disputa.

Resuelve con lectura visual a plena resolucion los casos donde el punto de
grounding rompe la continuidad de la trayectoria o discrepa >90 px de una
caja TP verificada en 1B:

- S1 74.0/74.2/74.4: el punto de 74.2 (374,498) rompe la tendencia
  derecha 74.0 (428,508) -> 74.4 (499,482).
- S3 169.2/169.4/169.6/169.8: 169.4 (804,594) y 169.6 (278,585) implican
  saltos de 254/526/770 px en 0.6 s (fisicamente imposibles).
- S4 194.0/194.2/194.4: puntos de grounding casi identicos (688,613);
  balon diminuto en plano tactico amplio.

Cada recorte se amplia x2 (sin reescalar el original: crop 640x360 ->
celda 1280x720 en la hoja) para ver el balon diminuto. Las hojas se
guardan en data/clips/work/exp1c/zoom/ (local, no en Git).
"""
import os
from PIL import Image, ImageDraw

LABELS = "data/clips/work/exp1c/../exp1b/labels"
OUT = "data/clips/work/exp1c/zoom"
os.makedirs(OUT, exist_ok=True)

# (etiqueta, fichero, recorte (x0,y0,x1,y1), punto grounding (x,y) o None)
CASES = {
    "s1-74": [
        ("74.0", "s1-f21.jpg", (200, 350, 840, 710), (428, 508)),
        ("74.2", "s1-f22.jpg", (200, 350, 840, 710), (374, 498)),
        ("74.4", "s1-f23.jpg", (200, 350, 840, 710), (499, 482)),
    ],
    "s3-169": [
        ("169.2", "s3-f27.jpg", (700, 400, 1340, 760), (1054, 638)),
        ("169.4", "s3-f28.jpg", (700, 400, 1340, 760), (804, 594)),
        ("169.6", "s3-f29.jpg", (700, 400, 1340, 760), (278, 585)),
        ("169.8", "s3-f30.jpg", (700, 400, 1340, 760), (1048, 608)),
    ],
    "s4-194": [
        ("194.0", "s4-f01.jpg", (368, 433, 1008, 793), (691, 613)),
        ("194.2", "s4-f02.jpg", (368, 433, 1008, 793), (689, 613)),
        ("194.4", "s4-f03.jpg", (368, 433, 1008, 793), (687, 613)),
    ],
}

for name, frames in CASES.items():
    cells = []
    for label, fname, (x0, y0, x1, y1), pt in frames:
        img = Image.open(os.path.join(LABELS, fname)).convert("RGB")
        crop = img.crop((x0, y0, x1, y1)).resize((1280, 720))
        d = ImageDraw.Draw(crop)
        # cruz amarilla en el punto de grounding (coordenadas de recorte)
        cx, cy = (pt[0] - x0) * 2, (pt[1] - y0) * 2
        d.line([(cx - 30, cy), (cx + 30, cy)], fill=(255, 255, 0), width=4)
        d.line([(cx, cy - 30), (cx, cy + 30)], fill=(255, 255, 0), width=4)
        d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12],
                  outline=(255, 255, 0), width=3)
        cells.append((label, crop))
    n = len(cells)
    cols = 2 if n <= 4 else 3
    rows = (n + cols - 1) // cols
    W, H = 1280, 720 + 44
    sheet = Image.new("RGB", (cols * W, rows * H), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    for i, (label, cell) in enumerate(cells):
        r, c = divmod(i, cols)
        sheet.paste(cell, (c * W, r * H + 44))
        d.text((c * W + 12, r * H + 6), f"t={label}s  (cruz amarilla = "
               "punto grounding)", fill=(255, 255, 0))
    sheet.save(os.path.join(OUT, f"zoom-{name}.jpg"), quality=92)
    print(f"zoom-{name}.jpg: {n} recortes x2")
