#!/usr/bin/env python3
"""Experimento 2 — Normaliza detecciones crudas al formato de evaluación.

Convierte un JSON de predicciones (formato de scripts/exp1b-predict.py o
scripts/exp2-cand1-predict.py) al formato que espera scripts/exp2-evaluate.py:
{"detector", "config", "detections": [{"t_abs", "x", "y", "conf"}]},
con (x, y) = centro de la caja.

Solo se conservan las detecciones de los fotogramas de la referencia
(red de 5 fps del CSV --ref): la definición de precisión del evaluador es
"detecciones de balón en fotogramas de referencia", así que el archivo
normalizado cubre exactamente esa red. El t_abs de salida es el tiempo
de referencia redondeado a 0,1 s, para que el emparejamiento del
evaluador (round(t_abs, 1)) sea exacto.

Uso:
    python3 scripts/exp2-normalize.py --pred docs/decisions/exp1b/pred1280-s1.json \
        --ref data/clips/work/exp2/ref-positions.csv --ball-cls "sports ball" \
        --detector yolo1280 --out docs/decisions/exp2/ball-detector/yolo1280.json
"""

import argparse
import csv
import json


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pred", action="append", required=True,
                    help="JSON de predicciones (repetible)")
    ap.add_argument("--ref", required=True, help="CSV de referencia")
    ap.add_argument("--ball-cls", required=True,
                    help="Nombre de la clase balón en el JSON de predicciones")
    ap.add_argument("--detector", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ref_times = set()
    with open(args.ref, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            ref_times.add(round(float(r["t_abs"]), 1))

    dets = []
    configs = []
    for path in args.pred:
        with open(path, encoding="utf-8") as fh:
            pred = json.load(fh)
        configs.append({k: pred["config"].get(k) for k in
                        ("weights", "imgsz", "conf", "iou", "classes",
                         "offset_seconds")})
        for fr in pred["frames"]:
            t_ref = round(float(fr["t_abs"]), 1)
            if t_ref not in ref_times:
                continue
            for d in fr.get("detections", []):
                if d["cls"] != args.ball_cls:
                    continue
                x0, y0, x1, y1 = d["bbox"]
                dets.append({
                    "t_abs": t_ref,
                    "x": round((x0 + x1) / 2, 1),
                    "y": round((y0 + y1) / 2, 1),
                    "conf": d["conf"],
                })
    out = {
        "detector": args.detector,
        "config": {"sources": args.pred, "ref": args.ref,
                   "ball_cls": args.ball_cls, "pred_configs": configs},
        "detections": dets,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(f"{args.detector}: {len(dets)} detecciones de balón en "
          f"{len(ref_times)} tiempos de referencia -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
