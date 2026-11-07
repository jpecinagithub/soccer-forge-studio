#!/usr/bin/env python3
"""Análisis del Experimento 1B (Soccer Forge Studio).

Separa lo que pierde YOLO de lo que descarta ByteTrack, para el balón.

Entradas:
  - docs/decisions/exp1b/pred640-s*.json  (predict crudo, conf 0.05)
  - docs/decisions/exp1b/track640-s*.json (ByteTrack, conf 0.25)
  - docs/decisions/exp1b/pred1280-s*.json / track1280-s*.json (cuando existan)
  - docs/decisions/exp1b/pred640-full.json + docs/decisions/exp1/full-b1.json
  - data/clips/work/exp1b/labels.csv (etiquetas manuales: V/?/N por fotograma)

Salidas: tablas por tramo y agregadas.
  - Paso 1: detecciones crudas vs tracks (balón), a igual y distinta confianza.
  - Paso 2: imgsz 640 vs 1280 (mismo material, misma confianza).
  - Paso 3: barrido de umbrales post-hoc sobre las detecciones crudas
    guardadas (0.05/0.10/0.25/0.40/0.60): recuperación del balón visible
    y falsos positivos (detecciones en fotogramas etiquetados N).
  - Paso 5: continuidad en tramos sin cortes (huecos de seguimiento del
    balón anclados a fotogramas etiquetados V; fragmentación de personas
    dentro de un plano continuo).

NO infiere eventos. La anotación v2 NO se usa para puntuar detecciones
(solo se usó para elegir tramos de vista de campo). Las etiquetas V/?/N
son revisión visual directa del autor del experimento.

Uso:
    python scripts/exp1b-analyze.py [--dir docs/decisions/exp1b]
"""

import argparse
import csv
import json
import os
import statistics

THRESHOLDS = [0.05, 0.10, 0.25, 0.40, 0.60]

# Tramos continuos sin cortes (verificados visualmente; v2 los agrupa
# en segmentos field-view más amplios, pero hay cortes dentro):
#   s1: 70-78 continuo; s2: corte entre 134.4 y 134.6 -> s2b 134.6-142;
#   s3: corte entre 164.6 y 164.8, y corte a close-up ~171.5 -> s3b 164.8-171.4;
#   s4: 194-202 continuo (pan/zoom, sin cortes).
CONTINUOUS = {
    "s1": (70.0, 78.0),
    "s2b": (134.6, 142.0),
    "s3b": (164.8, 171.4),
    "s4": (194.0, 202.0),
}
STRETCH_OF = {"s1": "s1", "s2": "s2", "s3": "s3", "s4": "s4"}


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def ball_dets(frame, min_conf=0.0):
    return [d for d in frame["detections"]
            if d["cls"] == "sports ball" and d["conf"] >= min_conf]


def person_dets(frame, min_conf=0.0):
    return [d for d in frame["detections"]
            if d["cls"] == "person" and d["conf"] >= min_conf]


def load_labels(path):
    labels = {}  # t_abs -> "V"/"?"/"N"
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            labels[float(row["t_abs"])] = row["ball"]
    return labels


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="docs/decisions/exp1b")
    args = ap.parse_args()
    d = args.dir

    labels = load_labels("data/clips/work/exp1b/labels.csv")
    labeled_v = sorted(t for t, v in labels.items() if v == "V")
    labeled_n = sorted(t for t, v in labels.items() if v == "N")
    print(f"Etiquetas: V={len(labeled_v)} ?= {sum(1 for v in labels.values() if v == '?')} "
          f"N={len(labeled_n)} (total {len(labels)})")

    # --- Carga de variantes ---
    variants = {}  # nombre -> {stretch: frames}
    for name, pattern in [
        ("P640", "pred640-{s}.json"),
        ("T640", "track640-{s}.json"),
        ("P1280", "pred1280-{s}.json"),
        ("T1280", "track1280-{s}.json"),
    ]:
        got = {}
        for s in ["s1", "s2", "s3", "s4"]:
            p = os.path.join(d, pattern.format(s=s))
            if os.path.exists(p):
                got[s] = load_json(p)["frames"]
        if got:
            variants[name] = got
            print(f"Variante {name}: tramos {sorted(got)}")

    def frames_of(variant, stretch):
        return variants[variant][stretch]

    def frame_at(variant, stretch, t_abs):
        for f in variants[variant][stretch]:
            if abs(f["t_abs"] - t_abs) < 0.02:
                return f
        return None

    # --- Paso 1: crudo vs track (balón), por tramo y agregado ---
    print("\n== Paso 1: detecciones crudas (P640, conf>=0.05) vs tracks (T640, conf 0.25) ==")
    print("Balón: fotogramas con >=1 detección y detecciones totales (800 fotogramas)")
    tot = {"P640": [0, 0], "T640": [0, 0], "P640@0.25": [0, 0]}
    for s in ["s1", "s2", "s3", "s4"]:
        p_frames = frames_of("P640", s)
        t_frames = frames_of("T640", s)
        p_fw = sum(1 for f in p_frames if ball_dets(f))
        t_fw = sum(1 for f in t_frames if ball_dets(f))
        p25_fw = sum(1 for f in p_frames if ball_dets(f, 0.25))
        p_n = sum(len(ball_dets(f)) for f in p_frames)
        t_n = sum(len(ball_dets(f)) for f in t_frames)
        p25_n = sum(len(ball_dets(f, 0.25)) for f in p_frames)
        tot["P640"][0] += p_fw; tot["P640"][1] += p_n
        tot["T640"][0] += t_fw; tot["T640"][1] += t_n
        tot["P640@0.25"][0] += p25_fw; tot["P640@0.25"][1] += p25_n
        print(f"  {s}: P640 {p_fw}/200 fotogramas ({p_fw/2:.1f}%), {p_n} det | "
              f"P640@0.25 {p25_fw}/200 ({p25_fw/2:.1f}%), {p25_n} det | "
              f"T640 {t_fw}/200 ({t_fw/2:.1f}%), {t_n} det")
    print(f"  TOTAL: P640 {tot['P640'][0]}/800 ({tot['P640'][0]/8:.1f}%), {tot['P640'][1]} det | "
          f"P640@0.25 {tot['P640@0.25'][0]}/800 ({tot['P640@0.25'][0]/8:.1f}%), {tot['P640@0.25'][1]} det | "
          f"T640 {tot['T640'][0]}/800 ({tot['T640'][0]/8:.1f}%), {tot['T640'][1]} det")
    print("  -> A igual confianza (0.25), el seguidor conserva "
          f"{tot['T640'][1]}/{tot['P640@0.25'][1]} detecciones de balón "
          f"({100*tot['T640'][1]/max(1, tot['P640@0.25'][1]):.1f}%) y "
          f"{tot['T640'][0]}/{tot['P640@0.25'][0]} fotogramas con balón "
          f"({100*tot['T640'][0]/max(1, tot['P640@0.25'][0]):.1f}%).")

    # --- Paso 3: barrido de umbrales sobre P640 y P1280 ---
    for pname in ["P640", "P1280"]:
        if pname not in variants:
            continue
        print(f"\n== Paso 3: barrido de umbrales ({pname}, detecciones crudas guardadas) ==")
        print("  umbral | fotogramas V con >=1 det (recuperación) | det en fotogramas N (FP) | "
              "det totales balón")
        for th in THRESHOLDS:
            rec = 0
            for t in labeled_v:
                s = "s1" if t < 100 else ("s2" if t < 150 else ("s3" if t < 180 else "s4"))
                f = frame_at(pname, s, t)
                if f is not None and ball_dets(f, th):
                    rec += 1
            fp_n = 0
            for t in labeled_n:
                s = "s1" if t < 100 else ("s2" if t < 150 else ("s3" if t < 180 else "s4"))
                f = frame_at(pname, s, t)
                if f is not None:
                    fp_n += len(ball_dets(f, th))
            tot_det = sum(len(ball_dets(f, th))
                          for s in variants[pname] for f in variants[pname][s])
            print(f"  {th:.2f}   | {rec}/{len(labeled_v)} ({100*rec/len(labeled_v):.1f}%) | "
                  f"{fp_n} | {tot_det}")

    # --- Paso 2: 640 vs 1280 (cuando exista P1280/T1280) ---
    if "P1280" in variants:
        print("\n== Paso 2: imgsz 640 vs 1280 (mismo material, misma confianza) ==")
        for th in [0.05, 0.25]:
            print(f"  -- umbral {th} (detecciones crudas) --")
            for s in ["s1", "s2", "s3", "s4"]:
                a = sum(1 for f in variants["P640"][s] if ball_dets(f, th))
                b = sum(1 for f in variants["P1280"][s] if ball_dets(f, th))
                na = sum(len(ball_dets(f, th)) for f in variants["P640"][s])
                nb = sum(len(ball_dets(f, th)) for f in variants["P1280"][s])
                print(f"    {s}: 640 {a}/200 fotogramas, {na} det | 1280 {b}/200, {nb} det")
        if "T1280" in variants:
            print("  -- tracks (conf 0.25) --")
            for s in ["s1", "s2", "s3", "s4"]:
                a = sum(1 for f in variants["T640"][s] if ball_dets(f))
                b = sum(1 for f in variants["T1280"][s] if ball_dets(f))
                print(f"    {s}: T640 {a}/200 fotogramas | T1280 {b}/200 fotogramas")
        # Recuperación del balón visible a 1280
        for pname in ["P1280", "T1280"]:
            if pname not in variants:
                continue
            th = 0.05 if pname.startswith("P") else 0.0
            rec = 0
            for t in labeled_v:
                s = "s1" if t < 100 else ("s2" if t < 150 else ("s3" if t < 180 else "s4"))
                f = frame_at(pname, s, t)
                if f is not None and ball_dets(f, th):
                    rec += 1
            print(f"  {pname}: recuperación del balón visible {rec}/{len(labeled_v)} "
                  f"({100*rec/len(labeled_v):.1f}%)")

    # --- Recuperación por tramo (P640 y T640) ---
    print("\n== Recuperación del balón visible por tramo (fotogramas V) ==")
    for pname, th in [("P640", 0.05), ("P640", 0.25), ("T640", 0.0)]:
        print(f"  {pname} (umbral {th}):")
        for s, (t0, t1) in [("s1", (70.0, 78.0)), ("s2", (134.0, 142.0)),
                            ("s3", (164.0, 172.0)), ("s4", (194.0, 202.0))]:
            vs = [t for t in labeled_v if t0 <= t < t1]
            rec = sum(1 for t in vs
                      if (f := frame_at(pname, s, t)) is not None and ball_dets(f, th))
            print(f"    {s}: {rec}/{len(vs)} ({100*rec/max(1, len(vs)):.1f}%)")

    # --- Paso 5: continuidad en tramos sin cortes ---
    print("\n== Paso 5: continuidad del balón en tramos sin cortes ==")
    for cname, (t0, t1) in CONTINUOUS.items():
        s = cname.rstrip("b") if cname.endswith("b") else cname
        if "T640" not in variants:
            break
        frames = [f for f in variants["T640"][s] if t0 <= f["t_abs"] < t1]
        vs = [t for t in labeled_v if t0 <= t < t1]
        # Huecos: rachas de fotogramas sin track de balón, ancladas a V en ambos extremos
        has_ball = [bool(ball_dets(f)) for f in frames]
        ts = [f["t_abs"] for f in frames]
        gaps = []
        i = 0
        while i < len(frames):
            if not has_ball[i]:
                j = i
                while j < len(frames) and not has_ball[j]:
                    j += 1
                # extremos etiquetados V
                before = [t for t in vs if t < ts[i]]
                after = [t for t in vs if t >= ts[j - 1]] if j <= len(frames) else []
                gaps.append((ts[i], ts[j - 1] if j > i else ts[i], j - i,
                             bool(before), bool(after)))
                i = j
            else:
                i += 1
        long_gaps = [g for g in gaps if g[2] >= 10]
        anchored = [g for g in long_gaps if g[3] and g[4]]
        print(f"  {cname} ({t0}-{t1}s, {len(frames)} fotogramas, {len(vs)} V): "
              f"fotogramas con track de balón: {sum(has_ball)}/{len(frames)} "
              f"({100*sum(has_ball)/max(1, len(frames)):.1f}%)")
        print(f"    huecos >=10 fotogramas (0,4 s) sin track de balón: {len(long_gaps)}; "
              f"anclados con V en ambos extremos: {len(anchored)}; "
              f"duraciones (fotogramas): {[g[2] for g in long_gaps]}")
        for g in anchored[:10]:
            print(f"      hueco {g[0]:.1f}-{g[1]:.1f}s ({g[2]} fotogramas, {g[2]/25:.1f} s) "
                  f"con balón visible antes y después")
        # Fragmentación de personas dentro del plano continuo
        ids_per_sec = {}
        for f in frames:
            sec = int(f["t_abs"])
            ids = {x["track_id"] for x in f["detections"]
                   if x["cls"] == "person" and x.get("track_id") is not None}
            ids_per_sec.setdefault(sec, set()).update(ids)
        n_ids = [len(v) for v in ids_per_sec.values()]
        print(f"    personas: ids distintos acumulados por segundo: {n_ids} "
              f"(media {statistics.mean(n_ids):.1f})")

    # --- Paso 5 (crudo): huecos en las detecciones crudas (sin seguidor) ---
    print("\n== Paso 5 (crudo): huecos sin detección de balón en detecciones crudas ==")
    for pname, th in [("P640", 0.05), ("P640", 0.25), ("P1280", 0.05), ("P1280", 0.25)]:
        if pname not in variants:
            continue
        print(f"  {pname} (umbral {th}):")
        for cname, (t0, t1) in CONTINUOUS.items():
            s = cname.rstrip("b") if cname.endswith("b") else cname
            frames = [f for f in variants[pname][s] if t0 <= f["t_abs"] < t1]
            vs = [t for t in labeled_v if t0 <= t < t1]
            has_ball = [bool(ball_dets(f, th)) for f in frames]
            ts = [f["t_abs"] for f in frames]
            gaps = []
            i = 0
            while i < len(frames):
                if not has_ball[i]:
                    j = i
                    while j < len(frames) and not has_ball[j]:
                        j += 1
                    before = [t for t in vs if t < ts[i]]
                    after = [t for t in vs if t >= ts[j - 1]] if j <= len(frames) else []
                    gaps.append((ts[i], ts[j - 1] if j > i else ts[i], j - i,
                                 bool(before), bool(after)))
                    i = j
                else:
                    i += 1
            long_gaps = [g for g in gaps if g[2] >= 25]  # >= 1 s
            anchored = [g for g in long_gaps if g[3] and g[4]]
            print(f"    {cname}: con balón {sum(has_ball)}/{len(frames)} "
                  f"({100*sum(has_ball)/max(1, len(frames)):.1f}%); "
                  f"huecos >=25 fotogramas (1 s): {len(long_gaps)}, "
                  f"anclados V-V: {len(anchored)}, "
                  f"duraciones (s): {[round(g[2]/25, 1) for g in long_gaps]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
