#!/usr/bin/env python3
"""Análisis descriptivo del Experimento 1 (fragmento) contra la referencia v2.

Compara SOLO categorías suficientemente anotadas:
- visibilidad del balón y densidad de personas por tipo de segmento
  (field-view / close-up / replay / excluded);
- presencia de detecciones de balón alrededor de los tiros puntuables
  de la ventana (ev-B1 penalti, ev-C1 tiro);
- continuidad del seguimiento (longitudes de track).

NO calcula F1 de pases, ni de seguimiento, ni de posiciones: los 5
eventos puntuables de B1 no lo permiten. NO usa la anotación para
seleccionar ventanas ni para ajustar nada: la ventana 35-65 s la fijó
el protocolo antes del análisis.

Uso:
    python scripts/exp1-analyze.py docs/decisions/exp1/frag-35-65.json
"""

import argparse
import json
import statistics
import sys

ANNOTATION = "docs/evaluation/B1-georgia-espana-annotation.json"


def seg_type_at(segments, t):
    for s in segments:
        if s["tStart"] <= t < s["tEnd"]:
            return s["type"]
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pred", help="JSON de predicciones")
    ap.add_argument("--t0", type=float, default=0.0, help="Inicio de ventana (t_abs)")
    ap.add_argument("--t1", type=float, default=237.24, help="Fin de ventana (t_abs)")
    args = ap.parse_args()
    pred = json.load(open(args.pred))
    ann = json.load(open(ANNOTATION))
    frames = [f for f in pred["frames"] if args.t0 <= f["t_abs"] < args.t1]
    segments = ann["segments"]

    # --- Por tipo de segmento ---
    by_type: dict[str, dict] = {}
    for f in frames:
        st = seg_type_at(segments, f["t_abs"])
        d = by_type.setdefault(st, {"n": 0, "persons": [], "ball_frames": 0})
        d["n"] += 1
        persons = [x for x in f["detections"] if x["cls"] == "person"]
        balls = [x for x in f["detections"] if x["cls"] == "sports ball"]
        d["persons"].append(len(persons))
        if balls:
            d["ball_frames"] += 1
    print("== Por tipo de segmento (t_abs %.2f-%.2f) ==" % (args.t0, args.t1))
    for st, d in sorted(by_type.items()):
        print(f"{st:10s} frames={d['n']:4d} personas/frame="
              f"{statistics.mean(d['persons']):5.2f} "
              f"balón visible={d['ball_frames'] / d['n'] * 100:5.1f}%")

    # --- Alrededor de los tiros puntuables de la ventana ---
    print("\n== Tiros puntuables en la ventana ==")
    for play in ann["plays"]:
        for ev in play["events"]:
            if ev["id"] not in ann["scoring"]["scoredEvents"]:
                continue
            if not (args.t0 <= ev["tStart"] < args.t1):
                continue
            for label, t in (("tStart", ev["tStart"]), ("tEnd", ev["tEnd"])):
                near = [f for f in frames if abs(f["t_abs"] - t) <= 1.0]
                ball = sum(1 for f in near
                           if any(x["cls"] == "sports ball" for x in f["detections"]))
                pers = statistics.mean(
                    sum(1 for x in f["detections"] if x["cls"] == "person")
                    for f in near) if near else 0
                print(f"{ev['id']} ({ev['type']}, {ev.get('result')}) {label}={t:.2f}s: "
                      f"fotogramas ±1s={len(near)}, con balón={ball}, "
                      f"personas/frame={pers:.1f}")

    # --- Continuidad del seguimiento ---
    print("\n== Continuidad (personas) ==")
    lengths = {}
    for f in frames:
        for x in f["detections"]:
            if x["cls"] == "person" and x["track_id"] is not None:
                lengths[x["track_id"]] = lengths.get(x["track_id"], 0) + 1
    vals = sorted(lengths.values())
    print(f"tracks distintos: {len(vals)} (en {args.t1 - args.t0:.0f} s; en campo hay ~22 personas + árbitros)")
    print(f"longitud media: {statistics.mean(vals):.1f} fotogramas "
          f"({statistics.mean(vals) / 25:.2f} s); mediana: {statistics.median(vals)}; "
          f"máx: {max(vals)}; de 1 fotograma: {sum(1 for v in vals if v == 1)}")
    # Cuántos tracks distintos aparecen en cada segundo (fragmentación visible)
    per_second = {}
    for f in frames:
        sec = int(f["t_abs"])
        ids = {x["track_id"] for x in f["detections"]
               if x["cls"] == "person" and x["track_id"] is not None}
        per_second.setdefault(sec, set()).update(ids)
    secs = sorted(per_second)
    print("tracks distintos acumulados por segundo (t_abs):",
          [len(per_second[s]) for s in secs][:60],
          "..." if len(secs) > 60 else "")

    # --- Balón: tracks ---
    print("\n== Balón: tracks ==")
    blengths = {}
    for f in frames:
        for x in f["detections"]:
            if x["cls"] == "sports ball" and x["track_id"] is not None:
                blengths[x["track_id"]] = blengths.get(x["track_id"], 0) + 1
    bvals = sorted(blengths.values())
    print(f"tracks de balón: {len(bvals)}; longitudes (fotogramas): {bvals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
