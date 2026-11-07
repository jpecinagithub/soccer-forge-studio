#!/usr/bin/env python3
"""Recuperación y precisión VERIFICADAS (Experimento 1B).

Lee docs/decisions/exp1b/box-verdicts.csv (juicios visuales por caja)
y los JSON de detecciones, y calcula mecánicamente:
  - recuperación verificada por umbral (fotogramas V con >=1 caja TP)
  - precisión por banda de confianza (cajas)
Además cruza cada caja registrada con el JSON correspondiente:
una detección con la misma confianza (+-0.015) debe existir en ese
fotograma y variante; si no, avisa (error de transcripción).

Uso: python scripts/exp1b-verified.py
"""

import csv
import json
import os
from collections import defaultdict

DIR = "docs/decisions/exp1b"
THRESHOLDS = [0.05, 0.10, 0.25, 0.40, 0.60]
BANDS = [(0.40, 1.01, ">=0.40"), (0.25, 0.40, "0.25-0.40"),
         (0.10, 0.25, "0.10-0.25"), (0.05, 0.10, "0.05-0.10")]


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def frame_at(frames, t_abs):
    for f in frames:
        if abs(f["t_abs"] - t_abs) < 0.02:
            return f
    return None


def main() -> int:
    variants = {}
    for name, pattern in [("P640", "pred640-{s}.json"),
                          ("P1280", "pred1280-{s}.json")]:
        got = {}
        for s in ["s1", "s2", "s3", "s4"]:
            p = os.path.join(DIR, pattern.format(s=s))
            if os.path.exists(p):
                got[s] = load_json(p)["frames"]
        variants[name] = got

    rows = []
    with open(os.path.join(DIR, "box-verdicts.csv"), newline="",
              encoding="utf-8") as fh:
        for row in csv.DictReader((l for l in fh if not l.startswith("#"))):
            rows.append(row)

    # --- Cruce con los JSON ---
    bad = 0
    for r in rows:
        t, s, v, conf = float(r["t_abs"]), r["stretch"], r["variant"], float(r["conf"])
        if conf == 0.0:
            continue  # conf no legible (171.6, segunda caja P1280)
        f = frame_at(variants[v][s], t)
        confs = [d["conf"] for d in f["detections"] if d["cls"] == "sports ball"] \
            if f is not None else []
        if not any(abs(c - conf) < 0.015 for c in confs):
            print(f"  AVISO: caja no encontrada en JSON: {r}")
            bad += 1
    print(f"Cruce con JSON: {len(rows)} cajas registradas, {bad} sin correspondencia.")

    # --- N total de fotogramas V ---
    labels = {}
    with open("data/clips/work/exp1b/labels.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            labels[float(row["t_abs"])] = row["ball"]
    n_v = sum(1 for v in labels.values() if v == "V")
    print(f"Fotogramas V: {n_v}")

    for variant in ["P640", "P1280"]:
        vr = [r for r in rows if r["variant"] == variant]
        tp = [r for r in vr if r["judgment"] == "TP"]
        fp = [r for r in vr if r["judgment"] == "FP"]
        q = [r for r in vr if r["judgment"] == "?"]
        print(f"\n== {variant}: {len(tp)} TP, {len(fp)} FP, {len(q)} ? "
              f"(precisión por caja {len(tp)}/{len(tp)+len(fp)} = "
              f"{100*len(tp)/max(1, len(tp)+len(fp)):.1f}%) ==")
        print("  Precisión por banda:")
        for lo, hi, name in BANDS:
            b_tp = [r for r in tp if lo <= float(r["conf"]) < hi]
            b_fp = [r for r in fp if lo <= float(r["conf"]) < hi]
            print(f"    {name}: {len(b_tp)} TP, {len(b_fp)} FP -> "
                  f"{100*len(b_tp)/max(1, len(b_tp)+len(b_fp)):.1f}%")
        print("  Recuperación verificada (fotogramas V con >=1 caja TP):")
        for th in THRESHOLDS:
            frames = {float(r["t_abs"]) for r in tp if float(r["conf"]) >= th}
            print(f"    umbral {th:.2f}: {len(frames)}/{n_v} ({100*len(frames)/n_v:.1f}%)")
        # Fotogramas V con solo FP (recuperación nominal falsa)
        tp_frames = {float(r["t_abs"]) for r in tp}
        fp_only = sorted({float(r["t_abs"]) for r in fp
                          if r["cat"] == "V" and float(r["t_abs"]) not in tp_frames})
        print(f"  Fotogramas V con SOLO cajas FP: {fp_only}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
