#!/usr/bin/env python3
"""Experimento 2 — Evaluación del enlazador CONGELADO (1C, g120-c8) sobre
detecciones de un detector, contra la referencia fiable.

Replica las métricas de la evaluación de 1C (docs/decisions/exp1c-*.md)
para poder comparar el mismo enlazador alimentado por otro detector:

- rec@tol (solo posiciones OBSERVADAS, nunca estimadas): fracción de
  fotogramas V de referencia con un track observado a <=tol px del balón.
- error rate: fracción de fotogramas V con al menos un track observado
  pero NINGUNO a <=50 px (el enlazador sigue un objeto equivocado).
- both: fotogramas V con un track correcto Y otro equivocado a la vez.
- no-track: fotogramas V sin ningún track observado.
- n_tracks, cambios de id entre fotogramas V consecutivos, hueco máximo
  (segundos sin track correcto observado, sobre la parrilla de 5 fps).

Uso:
    python3 scripts/exp2-evaluate-linker.py --ref data/clips/work/exp2/ref-positions-b1.csv \
        --link docs/decisions/exp1c/link-s1-g120-c8.json \
        --link docs/decisions/exp1c/link-s2-g120-c8.json \
        --label yolo-linker --out docs/decisions/exp2/ball-detector/linker-eval-b1.json
"""

import argparse
import csv
import json
import math
from collections import defaultdict


def load_ref(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["status"] == "V":
                rows.append({"t_abs": round(float(r["t_abs"]), 1),
                             "segment": r["segment"],
                             "x": float(r["x"]), "y": float(r["y"])})
    return rows


def load_link(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    # t_abs exacto (2 decimales; la parrilla de referencia, cada 0,2 s, es
    # subconjunto de la parrilla de 25 fps del enlazador) -> tracks
    by_t = {}
    for fr in d["frames"]:
        t = round(float(fr["t_abs"]), 2)
        tracks = []
        for tr in fr["tracks"]:
            x0, y0, x1, y1 = tr["bbox"]
            tracks.append({"tid": tr["track_id"],
                           "cx": (x0 + x1) / 2, "cy": (y0 + y1) / 2,
                           "status": tr["status"]})
        by_t[t] = tracks
    return d["config"].get("segment"), d.get("n_tracks", 0), by_t


def evaluate(ref, link_by_seg):
    """ref: lista de fotogramas V; link_by_seg: {seg: (n_tracks, by_t)}.
    Solo se evalúan los segmentos presentes en link_by_seg (ajuste o
    comprobación por separado)."""
    ref = [r for r in ref if r["segment"] in link_by_seg]
    n = len(ref)
    rec = {tol: 0 for tol in (25, 50, 100)}
    only_wrong = 0
    both = 0
    no_track = 0
    correct = 0
    # hueco máximo (sobre la parrilla ordenada de V) y cambios de id
    per_seg = defaultdict(list)
    for r in ref:
        per_seg[r["segment"]].append(r)
    max_gap_s = 0.0
    id_changes = 0
    for seg, rows in per_seg.items():
        rows.sort(key=lambda r: r["t_abs"])
        _, _, by_t = link_by_seg[seg]
        last_correct_tid = None
        gap = 0.0
        for r in rows:
            tracks = [t for t in by_t.get(round(r["t_abs"], 2), [])
                      if t["status"] == "observed"]
            dists = [(math.hypot(t["cx"] - r["x"], t["cy"] - r["y"]), t)
                     for t in tracks]
            ok = [d for d in dists if d[0] <= 50]
            if ok:
                correct += 1
                for tol in rec:
                    if min(d[0] for d in dists) <= tol:
                        rec[tol] += 1
                if len(dists) > len(ok):
                    both += 1
                best_tid = min(ok, key=lambda d: d[0])[1]["tid"]
                if last_correct_tid is not None and best_tid != last_correct_tid:
                    id_changes += 1
                last_correct_tid = best_tid
                gap = 0.0
            else:
                if tracks:
                    only_wrong += 1
                else:
                    no_track += 1
                last_correct_tid = None
                gap += 0.2
                max_gap_s = max(max_gap_s, gap)
    total_tracks = sum(v[1] for v in link_by_seg.values())
    return {
        "n_ref": n,
        "rec25": round(rec[25] / n, 3) if n else None,
        "rec50": round(rec[50] / n, 3) if n else None,
        "rec100": round(rec[100] / n, 3) if n else None,
        "correct_frames": correct,
        "only_wrong_frames": only_wrong,
        "error_rate": round(only_wrong / n, 3) if n else None,
        "both_frames": both,
        "no_track_frames": no_track,
        "n_tracks": total_tracks,
        "id_changes": id_changes,
        "max_gap_s": round(max_gap_s, 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--link", action="append", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seg-map", default="",
                    help="mapeo refseg=linkseg, coma (p. ej. s2b=s2,s3b=s3)")
    args = ap.parse_args()

    ref = load_ref(args.ref)
    seg_map = {}
    for pair in args.seg_map.split(","):
        if "=" in pair:
            a, b = pair.split("=", 1)
            seg_map[a.strip()] = b.strip()
    # aplicar el mapeo a los segmentos de la referencia
    for r in ref:
        r["segment"] = seg_map.get(r["segment"], r["segment"])
    link_by_seg = {}
    for path in args.link:
        seg, n_tracks, by_t = load_link(path)
        link_by_seg[seg] = (path, n_tracks, by_t)
    res = evaluate(ref, link_by_seg)
    res["label"] = args.label
    res["ref"] = args.ref
    res["links"] = args.link
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print(f"{args.label}: {json.dumps(res, indent=2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
