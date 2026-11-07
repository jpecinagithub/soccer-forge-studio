#!/usr/bin/env python3
"""Experimento 1C: diagnostico de movimiento de camara a partir de las
detecciones P1280 ya guardadas (sin repetir inferencia).

Para cada par de fotogramas consecutivos (25 fps) se emparejan las
cajas de persona (conf >= 0.5) por IoU voraz (>= 0.3) y se calcula la
mediana del desplazamiento de sus centros. Un desplazamiento mediano
grande y coherente indica paneo/zoom de la camara (que mueve TODAS
las posiciones en coords de imagen, incluido el balon); un
desplazamiento mediano ~0 con colas largas indica jugadores que se
mueven sobre camara estatica.

Uso:
    python scripts/exp1c-camera.py
"""
import json
import statistics
from pathlib import Path

BASE = Path("docs/decisions/exp1b")


def iou(a, b):
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return 0.0
    inter = w * h
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


def main() -> int:
    for seg in ("s1", "s2", "s3", "s4"):
        with open(BASE / f"pred1280-{seg}.json", encoding="utf-8") as fh:
            frames = json.load(fh)["frames"]
        medians = []
        worst = []
        for f0, f1 in zip(frames, frames[1:]):
            b0 = [d["bbox"] for d in f0["detections"]
                  if d["cls"] == "person" and d["conf"] >= 0.5]
            b1 = [d["bbox"] for d in f1["detections"]
                  if d["cls"] == "person" and d["conf"] >= 0.5]
            pairs = []
            for i, a in enumerate(b0):
                for j, b in enumerate(b1):
                    v = iou(a, b)
                    if v >= 0.3:
                        pairs.append((v, i, j))
            pairs.sort(reverse=True)
            used0, used1, disps = set(), set(), []
            for _v, i, j in pairs:
                if i in used0 or j in used1:
                    continue
                used0.add(i)
                used1.add(j)
                ax = (b0[i][0] + b0[i][2]) / 2
                ay = (b0[i][1] + b0[i][3]) / 2
                bx = (b1[j][0] + b1[j][2]) / 2
                by = (b1[j][1] + b1[j][3]) / 2
                disps.append(((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5)
            if disps:
                m = statistics.median(disps)
                medians.append(m)
                worst.append((m, f0["t_abs"], len(disps)))
        medians.sort()
        n = len(medians)
        worst.sort(reverse=True)
        print(f"{seg}: mediana del desplazamiento mediano = "
              f"{statistics.median(medians):.1f} px/fotograma "
              f"(p90={medians[int(n * 0.9)]:.1f}, max={medians[-1]:.1f}, "
              f"n={n})")
        print(f"   mayores saltos de camara: " +
              ", ".join(f"{t:.2f}s ({m:.0f}px, {k} cajas)"
                        for m, t, k in worst[:3]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
