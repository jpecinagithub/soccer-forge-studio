#!/usr/bin/env python3
"""Experimento 3 — Evaluación CORREGIDA de detecciones crudas de balón.

Corrige el defecto conocido del evaluador de exp2 (scripts/exp2-evaluate.py,
documentado en docs/decisions/exp2-ball-detector-2026-11-07.md §8 y en las
correcciones del usuario 2026-11-07): la precisión de exp2 era
tp_dets / total_dets, donde total_dets incluía detecciones en fotogramas O
que NO se contaban como falsos positivos. Es decir, mezclaba casos
evaluables y desconocidos: una detección en un fotograma donde el balón
está presente pero no es localizable penalizaba la precisión sin ser un
falso positivo demostrable.

CAMBIO (exp3, sobre resultados guardados, sin repetir inferencia):
- La referencia v3 (docs/decisions/exp3/ref-positions-*-v3.csv) separa los
  fotogramas O en AUSENTE CONFIRMADO (o_class=absent_confirmed: el balón
  no está en el fotograma) y NO LOCALIZABLE (o_class=not_localizable: el
  balón está en el fotograma — en la red, oculto en un tumulto, en vuelo —
  pero su posición no es determinable de forma fiable).
- Precisión adjudicable: tp_dets / (tp_dets + fp_V + fp_A), donde fp_V son
  las detecciones no-TP en fotogramas V y fp_A las detecciones en
  fotogramas de ausente confirmado (ahí cualquier detección ES un falso
  positivo, porque el balón no está). Las detecciones en fotogramas no
  localizables se publican APARTE como desconocidas (unknown_dets): no
  entran en el numerador ni en el denominador de precisión.
- Se conserva precision_legacy (definición exp2: tp_dets / total_dets)
  en la misma salida para la comparación antes/después.
- La recuperación (recall) solo usa fotogramas V, así que el cambio de
  criterio no la altera por sí mismo; SÍ cambia si la referencia v3
  corrige fotogramas (O->V o posiciones V): la salida registra n_V v3 y
  los cambios aplicados, y --legacy copia los valores publicados de exp2
  para la tabla antes/después.
- Subconjunto B3 independiente de YOLO (--subset): la recuperación sobre
  los 20 fotogramas V de B3 cuyas coordenadas NO derivan de propuestas
  YOLO (3 CORRECT + 7 resueltos desde FP + 10 interpolados; lista
  reconstruida de data/clips/work/exp2/b3-zoom-verdicts.csv y
  b3-interp.csv; ver docs/decisions/exp3/). Es un subconjunto útil de
  casos difíciles, NO una muestra sin sesgo (corrección del usuario
  2026-11-07). Con --subset-ext se añade la lista ampliada (n=22) con los
  dos V nuevos de exp3 (79.6, 96.4), cuyas posiciones se leyeron por zoom
  sin aceptar propuestas YOLO.

Uso:
    python3 scripts/exp3-evaluate.py --ref docs/decisions/exp3/ref-positions-b1-v3.csv \\
        --det docs/decisions/exp2/ball-detector/norm-yolo-b1.json \\
        --det docs/decisions/exp2/ball-detector/norm-cand1-b1.json \\
        --out docs/decisions/exp3/eval-corrected-b1.json
    python3 scripts/exp3-evaluate.py --ref docs/decisions/exp3/ref-positions-b3-v3.csv \\
        --det docs/decisions/exp2/ball-detector/norm-yolo-b3.json \\
        --det docs/decisions/exp2/ball-detector/norm-cand1-b3.json \\
        --subset 10.2,11.0,11.4,54.0,54.2,56.0,78.2,78.4,78.6,79.4,81.2,81.4,81.6,82.4,83.6,84.8,96.8,97.2,99.6,100.6 \\
        --subset-ext 10.2,11.0,11.4,54.0,54.2,56.0,78.2,78.4,78.6,79.4,79.6,81.2,81.4,81.6,82.4,83.6,84.8,96.4,96.8,97.2,99.6,100.6 \\
        --legacy docs/decisions/exp2/ball-detector/eval-b3.json \\
        --out docs/decisions/exp3/eval-corrected-b3.json
"""

import argparse
import csv
import json
import math

TOLS = (25, 50, 100)


def load_ref(path):
    """Devuelve (V, A, NL): listas de dicts con t_abs y (x, y) si V."""
    V, A, NL = [], [], []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            t = round(float(r["t_abs"]), 1)
            oc = r.get("o_class", "")
            if r["status"] == "V":
                V.append({"t_abs": t, "segment": r["segment"],
                          "x": float(r["x"]), "y": float(r["y"]),
                          "unc": float(r.get("unc", 15) or 15)})
            elif oc == "absent_confirmed":
                A.append({"t_abs": t, "segment": r["segment"]})
            else:  # O sin clase explícita se trata como no localizable
                NL.append({"t_abs": t, "segment": r["segment"]})
    return V, A, NL


def load_det(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    return d["detector"], d.get("config", {}), d["detections"]


def evaluate(V, A, NL, dets, conf, tol):
    """Recall sobre V; precisión SOLO sobre casos adjudicables (V + A);
    detecciones en NL aparte como desconocidas."""
    by_t = {}
    for d in dets:
        if d["conf"] >= conf:
            by_t.setdefault(round(d["t_abs"], 1), []).append(d)
    tp_frames = 0
    tp_dets = 0
    fp_V = 0
    errs = []
    for r in V:
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
        for d in cands:
            dist = math.hypot(d["x"] - r["x"], d["y"] - r["y"])
            if best is not None and d is best[1]:
                continue
            if dist > tol:
                fp_V += 1
    # Fotogramas de ausente confirmado: toda detección es FP demostrable.
    fp_A = sum(len(by_t.get(round(r["t_abs"], 1), [])) for r in A)
    # Fotogramas no localizables: desconocidas, fuera de la precisión.
    unknown_dets = sum(len(by_t.get(round(r["t_abs"], 1), [])) for r in NL)
    unknown_frames = sum(1 for r in NL if by_t.get(round(r["t_abs"], 1)))
    n = len(V)
    total_dets = sum(len(v) for v in by_t.values())
    adjudicable_dets = tp_dets + fp_V + fp_A
    errs_sorted = sorted(errs)
    med = errs_sorted[len(errs_sorted) // 2] if errs_sorted else None
    p90 = (errs_sorted[int(len(errs_sorted) * 0.9)]
           if errs_sorted else None)
    return {
        "conf": conf,
        "tol": tol,
        "n_ref_V": n,
        "n_absent": len(A),
        "n_unlocatable": len(NL),
        "recall": round(tp_frames / n, 3) if n else None,
        "recall_frames": tp_frames,
        "precision_adjudicable": (round(tp_dets / adjudicable_dets, 3)
                                  if adjudicable_dets else None),
        "precision_legacy_exp2": (round(tp_dets / total_dets, 3)
                                  if total_dets else None),
        "tp_dets": tp_dets,
        "fp_V_dets": fp_V,
        "fp_absent_dets": fp_A,
        "adjudicable_dets": adjudicable_dets,
        "unknown_dets_NL": unknown_dets,
        "unknown_frames_NL": unknown_frames,
        "total_dets": total_dets,
        "loc_err_median": round(med, 1) if med is not None else None,
        "loc_err_p90": round(p90, 1) if p90 is not None else None,
    }


def subset_recall(V, dets, conf, tol, subset):
    """Recuperación restringida a los fotogramas V de la lista subset."""
    sub = [r for r in V if r["t_abs"] in set(subset)]
    if not sub:
        return None
    by_t = {}
    for d in dets:
        if d["conf"] >= conf:
            by_t.setdefault(round(d["t_abs"], 1), []).append(d)
    hit = 0
    for r in sub:
        for d in by_t.get(round(r["t_abs"], 1), []):
            if math.hypot(d["x"] - r["x"], d["y"] - r["y"]) <= tol:
                hit += 1
                break
    return {"n": len(sub), "hits": hit,
            "recall": round(hit / len(sub), 3)}


def legacy_block(path):
    """Copia los valores publicados de exp2 (tol 50) para antes/después."""
    if not path:
        return None
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    out = {}
    for name, entry in d["detectors"].items():
        out[name] = {}
        for conf, by_tol in entry["by_conf"].items():
            m = by_tol["50"]
            out[name][conf] = {"recall": m["recall"],
                               "precision_legacy": m["precision"],
                               "tp_dets": m["tp_dets"],
                               "total_dets": m["total_dets"],
                               "n_ref_V": m["n_ref"]}
    return {"source": path, "tol": 50, "detectors": out}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--det", action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--confs", default="0.05,0.10,0.25,0.40,0.60")
    ap.add_argument("--subset", default="",
                    help="t_abs (coma) del subconjunto independiente")
    ap.add_argument("--subset-ext", default="",
                    help="t_abs (coma) del subconjunto ampliado con V nuevos exp3")
    ap.add_argument("--legacy", default="",
                    help="eval JSON de exp2 para la tabla antes/después")
    args = ap.parse_args()

    V, A, NL = load_ref(args.ref)
    confs = [float(c) for c in args.confs.split(",")]
    subset = [float(x) for x in args.subset.split(",") if x.strip()]
    subset_ext = [float(x) for x in args.subset_ext.split(",") if x.strip()]
    results = {"ref": args.ref, "n_ref_V": len(V),
               "n_absent_confirmed": len(A),
               "n_not_localizable": len(NL),
               "tols": list(TOLS),
               "method": ("precision sobre casos adjudicables (V + ausente "
                          "confirmado); detecciones en no-localizable aparte "
                          "como desconocidas; ver cabecera del script"),
               "legacy_exp2_tol50": legacy_block(args.legacy),
               "detectors": {}}
    if subset:
        results["subset_independent"] = {
            "t_abs": subset, "n": len(subset),
            "note": ("subconjunto util de casos dificiles, NO muestra sin "
                     "sesgo (correccion del usuario 2026-11-07)")},
    if subset_ext:
        results["subset_independent_ext"] = {
            "t_abs": subset_ext, "n": len(subset_ext),
            "note": "subset de 20 + V nuevos exp3 (79.6, 96.4)"}
    for path in args.det:
        name, config, dets = load_det(path)
        entry = {"config": config, "file": path, "by_conf": {}}
        for conf in confs:
            entry["by_conf"][str(conf)] = {
                str(tol): evaluate(V, A, NL, dets, conf, tol) for tol in TOLS
            }
            if subset:
                entry["by_conf"][str(conf)]["subset_independent"] = {
                    str(tol): subset_recall(V, dets, conf, tol, subset)
                    for tol in TOLS}
            if subset_ext:
                entry["by_conf"][str(conf)]["subset_independent_ext"] = {
                    str(tol): subset_recall(V, dets, conf, tol, subset_ext)
                    for tol in TOLS}
        results["detectors"][name] = entry
        print(f"{name}: {len(dets)} detecciones, ref V={len(V)} "
              f"A={len(A)} NL={len(NL)}")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"escrito {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
