#!/usr/bin/env python3
"""Experimento 2 — Evaluación de detecciones crudas de balón contra la referencia.

Compara detecciones crudas (sin seguidor) de varios detectores contra la
referencia fiable (posiciones a resolución original, con incertidumbre
explícita). Métricas por detector y por umbral de confianza (barrido
post-hoc sobre las detecciones guardadas):

- recuperación (recall): fotogramas V con >=1 detección a <=tol px del balón
- precisión: detecciones de balón que caen a <=tol px de un balón V,
  sobre todas las detecciones de balón en fotogramas de referencia
- error de localización: distancia mediana (y p90) de la detección
  emparejada al balón verdadero
- falsos positivos por fotograma (detecciones sin balón V cerca)

La tolerancia principal es 50 px (la referencia nueva tiene ruido ~10-15 px
tras verificación a resolución original, a diferencia de los ~40 px de 1C);
se informa también a 25 y 100 px como sensibilidad.

Formato de entrada (normalizado): JSON con {"detector": str, "config": {...},
"detections": [{"t_abs": float, "x": float, "y": float, "conf": float}]}.
La conversión desde el formato propio de cada detector se hace en scripts
separados (p. ej. exp2-yolo-norm.py, exp2-<candidato>-norm.py).

Uso:
    python3 scripts/exp2-evaluate.py --ref data/clips/work/exp2/ref-positions.csv \
        --det docs/decisions/exp2/ball-detector/yolo1280.json \
        --det docs/decisions/exp2/ball-detector/cand1.json \
        --out docs/decisions/exp2/ball-detector/evaluation.json
"""

import argparse
import csv
import json
import math

TOLS = (25, 50, 100)


def load_ref(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["status"] == "V":
                rows.append({
                    "t_abs": float(r["t_abs"]),
                    "segment": r["segment"],
                    "x": float(r["x"]),
                    "y": float(r["y"]),
                    "unc": float(r.get("unc", 15)),
                })
    return rows


def load_det(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    return d["detector"], d.get("config", {}), d["detections"]


def evaluate(ref, dets, conf, tol):
    """Recall/precisión/error para un umbral de confianza y una tolerancia."""
    by_t = {}
    for d in dets:
        if d["conf"] >= conf:
            by_t.setdefault(round(d["t_abs"], 1), []).append(d)
    tp_frames = 0
    tp_dets = 0
    fp_dets = 0
    errs = []
    for r in ref:
        cands = by_t.get(round(r["t_abs"], 1), [])
        best = None
        for d in cands:
            dist = math.hypot(d["x"] - r["x"], d["y"] - r["y"])
            if best is None or dist < best[0]:
                best = (dist, d)
        if best is not None and best[0] <= tol:
            tp_frames += 1
            tp_dets += 1
            errs.append(best[0])
        # resto de detecciones de este fotograma: FP salvo la emparejada
        for d in cands:
            dist = math.hypot(d["x"] - r["x"], d["y"] - r["y"])
            if best is not None and d is best[1]:
                continue
            if dist > tol:
                fp_dets += 1
    n = len(ref)
    total_dets = sum(len(v) for v in by_t.values())
    errs_sorted = sorted(errs)
    med = errs_sorted[len(errs_sorted) // 2] if errs_sorted else None
    p90 = (errs_sorted[int(len(errs_sorted) * 0.9)]
           if errs_sorted else None)
    return {
        "conf": conf,
        "tol": tol,
        "n_ref": n,
        "recall": round(tp_frames / n, 3) if n else None,
        "precision": round(tp_dets / total_dets, 3) if total_dets else None,
        "tp_dets": tp_dets,
        "fp_dets": fp_dets,
        "fp_per_frame": round(fp_dets / n, 3) if n else None,
        "total_dets": total_dets,
        "loc_err_median": round(med, 1) if med is not None else None,
        "loc_err_p90": round(p90, 1) if p90 is not None else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--det", action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--confs", default="0.05,0.10,0.25,0.40,0.60")
    args = ap.parse_args()

    ref = load_ref(args.ref)
    confs = [float(c) for c in args.confs.split(",")]
    results = {"ref": args.ref, "n_ref": len(ref),
               "tols": list(TOLS), "detectors": {}}
    for path in args.det:
        name, config, dets = load_det(path)
        entry = {"config": config, "file": path, "by_conf": {}}
        for conf in confs:
            entry["by_conf"][str(conf)] = {
                str(tol): evaluate(ref, dets, conf, tol) for tol in TOLS
            }
        results["detectors"][name] = entry
        print(f"{name}: {len(dets)} detecciones, ref n={len(ref)}")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"escrito {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
