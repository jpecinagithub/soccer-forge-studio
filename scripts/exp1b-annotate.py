#!/usr/bin/env python3
"""Hojas anotadas para verificación posicional (Experimento 1B).

Dibuja las cajas de balón de cada variante sobre los fotogramas
etiquetados, para juzgar visualmente si cada detección cae sobre el
balón real (TP) o no (FP):
  - verde:  P640 crudo, conf >= 0.25
  - amarillo: P640 crudo, 0.05 <= conf < 0.25
  - rojo:   T640 track, conf 0.25 (todas las que conserva)
  - azul:   P1280 crudo, conf >= 0.25 (cuando exista)
  - cian:   P1280 crudo, 0.05 <= conf < 0.25 (cuando exista)
  - magenta: T1280 track (cuando exista)

Se anotan los fotogramas etiquetados (V/?/N) que tienen al menos una
detección de balón en alguna variante, más los fotogramas V sin
detección (FN de referencia, sin cajas).

Uso:
    python scripts/exp1b-annotate.py [--dir docs/decisions/exp1b]
"""

import argparse
import csv
import json
import os

from PIL import Image, ImageDraw, ImageFont

LABELS_DIR = "data/clips/work/exp1b/labels"
OUT_DIR = "data/clips/work/exp1b/annotated"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def frame_at(frames, t_abs):
    for f in frames:
        if abs(f["t_abs"] - t_abs) < 0.02:
            return f
    return None


def ball_boxes(frame, min_conf=0.0):
    if frame is None:
        return []
    return [d for d in frame["detections"]
            if d["cls"] == "sports ball" and d["conf"] >= min_conf]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="docs/decisions/exp1b")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)

    labels = {}
    with open("data/clips/work/exp1b/labels.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            labels[float(row["t_abs"])] = (row["stretch"], row["ball"])

    variants = {}
    for name, pattern in [("P640", "pred640-{s}.json"),
                          ("T640", "track640-{s}.json"),
                          ("P1280", "pred1280-{s}.json"),
                          ("T1280", "track1280-{s}.json")]:
        got = {}
        for s in ["s1", "s2", "s3", "s4"]:
            p = os.path.join(args.dir, pattern.format(s=s))
            if os.path.exists(p):
                got[s] = load_json(p)["frames"]
        if got:
            variants[name] = got

    # Fotogramas a anotar: etiquetados con >=1 detección de balón en
    # alguna variante, + todos los N, + una muestra de V sin detección.
    todo = []
    for t, (s, cat) in sorted(labels.items()):
        boxes = {}
        for name, v in variants.items():
            f = frame_at(v[s], t)
            boxes[name] = ball_boxes(f, 0.05 if name.startswith("P") else 0.0)
        n = sum(len(b) for b in boxes.values())
        if n > 0 or cat in ("N", "?"):
            todo.append((t, s, cat, boxes))
    print(f"Fotogramas a anotar: {len(todo)}")

    font = ImageFont.truetype(FONT, 26)
    font_big = ImageFont.truetype(FONT, 34)
    sheets = []
    CELL_W, CELL_H, BAR = 960, 540, 48
    for idx in range(0, len(todo), 4):
        chunk = todo[idx:idx + 4]
        sheet = Image.new("RGB", (CELL_W * 2, (CELL_H + BAR) * 2), "black")
        d = ImageDraw.Draw(sheet)
        for j, (t, s, cat, boxes) in enumerate(chunk):
            # fotograma original (5 fps) más cercano a t
            k = round((t - {"s1": 70.0, "s2": 134.0, "s3": 164.0, "s4": 194.0}[s]) / 0.2)
            fn = os.path.join(LABELS_DIR, f"{s}-f{k+1:02d}.jpg")
            img = Image.open(fn).convert("RGB")
            dd = ImageDraw.Draw(img)
            colors = {"P640_hi": (0, 255, 0), "P640_lo": (255, 255, 0),
                      "T640": (255, 0, 0), "P1280_hi": (0, 120, 255),
                      "P1280_lo": (0, 255, 255), "T1280": (255, 0, 255)}
            drawn = []
            for b in boxes.get("P640", []):
                c = "P640_hi" if b["conf"] >= 0.25 else "P640_lo"
                x0, y0, x1, y1 = b["bbox"]
                dd.rectangle([x0, y0, x1, y1], outline=colors[c], width=4)
                dd.text((x0 + 2, max(0, y0 - 30)), f"P640 {b['conf']:.2f}",
                        fill=colors[c], font=font)
                drawn.append(f"P640:{b['conf']:.2f}")
            for b in boxes.get("P1280", []):
                c = "P1280_hi" if b["conf"] >= 0.25 else "P1280_lo"
                x0, y0, x1, y1 = b["bbox"]
                dd.rectangle([x0, y0, x1, y1], outline=colors[c], width=4)
                dd.text((x0 + 2, max(0, y0 - 30)), f"P1280 {b['conf']:.2f}",
                        fill=colors[c], font=font)
                drawn.append(f"P1280:{b['conf']:.2f}")
            for b in boxes.get("T640", []):
                x0, y0, x1, y1 = b["bbox"]
                dd.rectangle([x0, y0, x1, y1], outline=colors["T640"], width=4)
                dd.text((x0 + 2, max(0, y0 - 30)), f"T640 {b['conf']:.2f} id{b.get('track_id')}",
                        fill=colors["T640"], font=font)
                drawn.append(f"T640:{b['conf']:.2f}")
            for b in boxes.get("T1280", []):
                x0, y0, x1, y1 = b["bbox"]
                dd.rectangle([x0, y0, x1, y1], outline=colors["T1280"], width=4)
                dd.text((x0 + 2, max(0, y0 - 30)), f"T1280 {b['conf']:.2f} id{b.get('track_id')}",
                        fill=colors["T1280"], font=font)
                drawn.append(f"T1280:{b['conf']:.2f}")
            img = img.resize((CELL_W, CELL_H))
            x, y = (j % 2) * CELL_W, (j // 2) * (CELL_H + BAR)
            d.rectangle([x, y, x + CELL_W, y + BAR], fill=(20, 20, 20))
            d.text((x + 8, y + 8), f"t={t:.1f}s ({s}, {cat})  " + " ".join(drawn),
                   fill=(255, 255, 0), font=font_big)
            sheet.paste(img, (x, y + BAR))
        out = os.path.join(OUT_DIR, f"sheet-{idx//4+1:02d}.jpg")
        sheet.save(out, quality=88)
        sheets.append(out)
        print(out, len(chunk), "frames")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
