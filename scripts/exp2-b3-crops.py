#!/usr/bin/env python3
"""Experimento 2 — Hojas de anotación de B3 (comprobación) a resolución original.

Para cada fotograma a 5 fps de los segmentos B3, toma la detección de balón
de mayor confianza de YOLO 1280 (pred1280-c*.json, solo como PROPUESTA de
dónde mirar) y recorta 480x480 a resolución original centrado en ella, con
una cruz en el centro de la detección. El anotador verifica visualmente si
el balón está ahí y corrige su posición; si el recorte no contiene el balón,
el fotograma se revisa en el fotograma completo (segunda pasada).

Las detecciones YOLO solo eligen dónde mirar primero: cada posición final
se determina por verificación visual a resolución original. Los fotogramas
sin ninguna detección se anotan directamente sobre el fotograma completo
(hojas *_nofull.jpg).

Uso:
    python3 scripts/exp2-b3-crops.py --pred docs/decisions/exp2/ball-detector/pred1280-c1.json \
        --clip data/clips/espana-bulgaria-rfef.mp4 --seg c1
Salida:
    data/clips/work/exp2/b3-verify/<seg>-sheet-NN.jpg   (recortes con propuesta)
    data/clips/work/exp2/b3-verify/<seg>-nofull-NN.jpg  (fotogramas sin detección)
    data/clips/work/exp2/b3-verify/<seg>-crops.csv     (t_abs, x_det, y_det, ox, oy)
"""

import argparse
import csv
import json
import os
import subprocess

from PIL import Image, ImageDraw

CROP = 480
COLS, ROWS = 4, 3
PER_SHEET = COLS * ROWS


def extract_frame(clip: str, t_abs: float, out: str) -> None:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t_abs:.2f}", "-i", clip,
         "-frames:v", "1", "-f", "image2", "-c", "png", out],
        check=True,
    )


def ball_detections(frame: dict):
    out = []
    for d in frame.get("detections", []):
        if d["cls"] == "sports ball":
            x0, y0, x1, y1 = d["bbox"]
            out.append({
                "cx": (x0 + x1) / 2,
                "cy": (y0 + y1) / 2,
                "conf": d["conf"],
                "bbox": d["bbox"],
            })
    return sorted(out, key=lambda b: -b["conf"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--seg", required=True)
    ap.add_argument("--step", type=float, default=0.2,
                    help="Paso de anotación en segundos (5 fps)")
    args = ap.parse_args()

    with open(args.pred, encoding="utf-8") as fh:
        pred = json.load(fh)
    offset = pred["config"]["offset_seconds"]
    frames = pred["frames"]
    # índice por t_rel redondeado a 0.01
    by_trel = {round(f["t_rel"], 2): f for f in frames}

    outdir = "data/clips/work/exp2/b3-verify"
    os.makedirs(outdir, exist_ok=True)

    t = 0.0
    dur = pred["video"]["duration_seconds"]
    crops = []   # (imagen, t_abs, ox, oy, det|None)
    nodet = []   # (imagen full 960x540, t_abs)
    while t < dur - 1e-6:
        t_abs = offset + t
        fr = by_trel.get(round(t, 2))
        dets = ball_detections(fr) if fr else []
        frame_png = f"/tmp/exp2-b3-{args.seg}-{t:.1f}.png"
        extract_frame(args.clip, t_abs, frame_png)
        im = Image.open(frame_png).convert("RGB")
        W, H = im.size
        if dets:
            best = dets[0]
            cx, cy = best["cx"], best["cy"]
            ox = min(max(int(cx) - CROP // 2, 0), W - CROP)
            oy = min(max(int(cy) - CROP // 2, 0), H - CROP)
            crop = im.crop((ox, oy, ox + CROP, oy + CROP))
            d = ImageDraw.Draw(crop)
            px, py = int(cx) - ox, int(cy) - oy
            d.line([(px - 20, py), (px + 20, py)], fill=(255, 0, 0), width=3)
            d.line([(px, py - 20), (px, py + 20)], fill=(255, 0, 0), width=3)
            d.ellipse([(px - 12, py - 12), (px + 12, py + 12)],
                      outline=(255, 0, 0), width=2)
            d.rectangle([(0, 0), (150, 26)], fill=(0, 0, 0))
            d.text((4, 6), f"{t_abs:.1f}s conf {best['conf']:.2f}",
                   fill=(255, 255, 0))
            crops.append((crop, t_abs, ox, oy, best))
        else:
            small = im.resize((960, 540))
            d = ImageDraw.Draw(small)
            d.rectangle([(0, 0), (120, 26)], fill=(0, 0, 0))
            d.text((4, 6), f"{t_abs:.1f}s SIN-DET", fill=(255, 255, 0))
            nodet.append((small, t_abs))
        os.remove(frame_png)
        t = round(t + args.step, 2)

    with open(os.path.join(outdir, f"{args.seg}-crops.csv"), "w",
              newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["t_abs", "x_det", "y_det", "conf_det", "ox", "oy"])
        for crop, t_abs, ox, oy, best in crops:
            w.writerow([f"{t_abs:.1f}", f"{best['cx']:.1f}",
                        f"{best['cy']:.1f}", best["conf"], ox, oy])

    for s in range((len(crops) + PER_SHEET - 1) // PER_SHEET):
        chunk = crops[s * PER_SHEET:(s + 1) * PER_SHEET]
        sheet = Image.new("RGB", (COLS * CROP, ROWS * CROP), "white")
        for j, (crop, t_abs, ox, oy, best) in enumerate(chunk):
            sheet.paste(crop, ((j % COLS) * CROP, (j // COLS) * CROP))
        path = os.path.join(outdir, f"{args.seg}-sheet-{s + 1:02d}.jpg")
        sheet.save(path, quality=92)
        print(path, len(chunk), "recortes")
    # hojas de fotogramas sin detección: 2x2 a 960x540
    for s in range((len(nodet) + 3) // 4):
        chunk = nodet[s * 4:(s + 1) * 4]
        sheet = Image.new("RGB", (2 * 960, 2 * 540), "white")
        for j, (small, t_abs) in enumerate(chunk):
            sheet.paste(small, ((j % 2) * 960, (j // 2) * 540))
        path = os.path.join(outdir, f"{args.seg}-nofull-{s + 1:02d}.jpg")
        sheet.save(path, quality=92)
        print(path, len(chunk), "sin detección")
    print(f"{args.seg}: {len(crops)} con propuesta, {len(nodet)} sin detección")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
