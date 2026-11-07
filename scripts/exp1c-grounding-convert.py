#!/usr/bin/env python3
"""Conversión de puntos de visual_grounding (hojas 1C) a coordenadas
originales 1920x1080 y cruce con las verificaciones de 1B.

Las hojas son de 2880x1168: 3 columnas x 960 px, 2 filas x 584 px
(barra de 44 px arriba de cada celda). Coordenadas normalizadas
0-1000 del grounding -> celda -> original (factor 2).

Cruces:
- labels.csv de 1B (V/?/N a 2,5 fps): el estado debe ser coherente.
- box-verdicts.csv de 1B: centros de cajas P1280 verificadas TP
  en los fotogramas coincidentes; la distancia al punto de grounding
  debe ser pequeña (<30 px) si ambos miran al mismo balón.

Uso:
    python scripts/exp1c-grounding-convert.py
"""

import csv
import json
import math

# (hoja, [(t_abs, x_norm, y_norm), ...]) en el orden de las celdas
SHEETS = {
    1: [(70.0, 50, 350), (70.2, 392, 338), (70.4, 716, 321),
        (70.6, 46, 818), (70.8, 390, 810), (71.0, 704, 760)],
    2: [(71.2, 40, 270), (71.4, 373, 265), (71.6, 707, 261),
        (71.8, 41, 765), (72.0, 381, 761), (72.2, 713, 757)],
    3: [(72.4, 46, 262), (72.6, 381, 261), (72.8, 714, 262),
        (73.0, 52, 765), (73.2, 389, 765), (73.4, 723, 767)],
    4: [(73.6, 54, 262), (73.8, 402, 258), (74.0, 741, 255),
        (74.2, 65, 751), (74.4, 420, 744), (74.6, 757, 737)],
    5: [(74.8, 78, 239), (75.0, 410, 238), (75.2, 731, 244),
        (75.4, 64, 739), (75.6, 423, 727), (75.8, 766, 735)],
    6: [(76.0, 117, 248), (76.2, 464, 259), (76.4, 810, 265),
        (76.6, 142, 785), (76.8, 488, 786), (77.0, 833, 786)],
    7: [(77.2, 176, 286), (77.4, 519, 289), (77.6, 857, 294),
        (77.8, 189, 779), (134.6, 560, 783), (134.8, 884, 789)],
    8: [(135.0, 216, 305), (135.2, 552, 308), (135.4, 893, 300),
        (135.6, 250, 808), (135.8, 581, 806), (136.0, 930, 795)],
    9: [(136.2, 254, 284), (136.4, 581, 287), (136.6, 916, 282),
        (136.8, 262, 777), (137.0, 601, 778), (137.2, 938, 772)],
    10: [(137.4, 273, 280), (137.6, 600, 285), (137.8, 928, 296),
         (138.0, 278, 796), (138.2, 614, 797), (138.4, 941, 794)],
    11: [(138.6, 270, 322), (138.8, 600, 318), (139.0, 922, 316),
         (139.2, 276, 796), (139.4, 606, 791), (139.6, 930, 789)],
    12: [(139.8, 238, 294), (140.0, 575, 297), (140.2, 912, 299),
         (140.4, 252, 797), (140.6, 588, 799), (140.8, 925, 801)],
    13: [(141.0, 238, 298), (141.2, 578, 291), (141.4, 915, 290),
         (141.6, 258, 774), (141.8, 597, 778), (164.8, 865, 810)],
    14: [(165.0, 188, 312), (165.2, 533, 313), (165.4, 868, 312),
         (165.6, 206, 811), (165.8, 542, 808), (166.0, 866, 812)],
    15: [(166.2, 213, 308), (166.4, 545, 318), (166.6, 890, 315),
         (166.8, 198, 795), (167.0, 540, 795), (167.2, 873, 788)],
    16: [(167.4, 217, 328), (167.6, 548, 326), (167.8, 882, 328),
         (168.0, 206, 818), (168.2, 540, 802), (168.4, 872, 812)],
    17: [(168.6, 176, 318), (168.8, 508, 326), (169.0, 848, 334),
         (169.2, 183, 811), (169.4, 473, 792), (169.6, 715, 788)],
    18: [(169.8, 182, 298), (170.0, 503, 306), (170.2, 904, 314),
         (170.4, 252, 812), (170.6, 598, 832), (170.8, 938, 828)],
    19: [(171.0, 254, 322), (171.2, 569, 324), (171.4, 892, 312),
         (194.0, 120, 800), (194.2, 453, 800), (194.4, 786, 800)],
    20: [(194.6, 102, 141), (194.8, 452, 150), (195.0, 790, 162),
         (195.2, 124, 678), (195.4, 458, 705), (195.6, 787, 740)],
    21: [(195.8, 115, 290), (196.0, 460, 330), (196.2, 809, 358),
         (196.4, 152, 884), (196.6, 495, 880), (196.8, 829, 880)],
    22: [(197.0, 170, 385), (197.2, 506, 406), (197.4, 842, 413),
         (197.6, 181, 913), (197.8, 518, 910), (198.0, 849, 909)],
    23: [(198.2, 184, 408), (198.4, 521, 411), (198.6, 840, 390),
         (198.8, 186, 888), (199.0, 536, 865), (199.2, 886, 842)],
    24: [(199.4, 197, 331), (199.6, 528, 326), (199.8, 858, 322),
         (200.0, 199, 810), (200.2, 531, 802), (200.4, 866, 800)],
    25: [(200.6, 237, 302), (200.8, 568, 300), (201.0, 898, 298),
         (201.2, 240, 796), (201.4, 572, 794), (201.6, 904, 792)],
    26: [(201.8, 236, 313)],
}

SHEET_W, SHEET_H = 2880, 1168
CELL_W, CELL_H, BAR = 960, 540, 44


def to_orig(xn, yn):
    col = min(2, int(xn // (1000 / 3)))
    row = 0 if yn < 500 else 1
    cell_x = xn / 1000 * SHEET_W - col * CELL_W
    cell_y = yn / 1000 * SHEET_H - row * (CELL_H + BAR) - BAR
    return round(cell_x * 2), round(cell_y * 2)


def main() -> int:
    pts = {}
    for sheet, cells in SHEETS.items():
        for t, xn, yn in cells:
            pts[round(t, 1)] = to_orig(xn, yn)
    print(f"Puntos convertidos: {len(pts)}")

    # Cruce 1: etiquetas 1B (V/?/N a 2,5 fps)
    labels = {}
    with open("data/clips/work/exp1b/labels.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            labels[float(row["t_abs"])] = row["ball"]

    # Cruce 2: cajas P1280 verificadas TP (centros). box-verdicts.csv no
    # lleva bbox: se recupera del JSON P1280 por (t_abs, conf ±0.015).
    import json as _json

    def load_pred(seg):
        with open(f"docs/decisions/exp1b/pred1280-{seg}.json",
                  encoding="utf-8") as fh:
            return _json.load(fh)["frames"]

    preds = {s: load_pred(s) for s in ("s1", "s2", "s3", "s4")}

    def frame_at(seg, t):
        for f in preds[seg]:
            if abs(f["t_abs"] - t) < 0.02:
                return f
        return None

    tp = {}
    with open("docs/decisions/exp1b/box-verdicts.csv", newline="",
              encoding="utf-8") as fh:
        rows = [ln for ln in fh if not ln.startswith("#")]
    for row in csv.DictReader(rows):
        if row["variant"] == "P1280" and row["judgment"] == "TP":
            t = float(row["t_abs"])
            f = frame_at(row["stretch"], t)
            if f is None:
                continue
            cands = [d for d in f["detections"]
                     if d["cls"] == "sports ball"
                     and abs(d["conf"] - float(row["conf"])) <= 0.015]
            for d in cands:
                x0, y0, x1, y1 = d["bbox"]
                tp.setdefault(t, []).append(((x0 + x1) / 2, (y0 + y1) / 2,
                                             d["conf"]))
    print(f"Fotogramas con TP P1280: {len(tp)}")

    print("\nt_abs | grounding (x,y) | label1B | TP P1280 centros | dist min")
    bad = []
    for t in sorted(pts):
        x, y = pts[t]
        lab = labels.get(t, "-")
        tps = tp.get(t, [])
        if tps:
            dmin = min(math.hypot(x - cx, y - cy) for cx, cy, _ in tps)
            desc = "; ".join(f"({cx:.0f},{cy:.0f})@{c:.2f}" for cx, cy, c in tps)
        else:
            dmin, desc = None, "-"
        flag = ""
        if dmin is not None and dmin > 30:
            flag = "  <-- REVISAR: grounding lejos del TP verificado"
            bad.append(t)
        if lab == "N":
            flag += "  <-- REVISAR: label N pero grounding da punto"
            bad.append(t)
        print(f"{t:6.1f} | ({x:4d},{y:4d}) | {lab:>2} | {desc} | "
              f"{dmin if dmin is None else round(dmin, 1)}{flag}")

    # Saltos frame a frame (por subtramo continuo) > 120 px / 0,2 s
    print("\nSaltos >120 px entre fotogramas consecutivos de 5 fps (mismo subtramo):")
    segs = [("s1", 70.0, 77.8), ("s2b", 134.6, 141.8),
            ("s3b", 164.8, 171.4), ("s4", 194.0, 201.8)]
    for name, t0, t1 in segs:
        ts = sorted(t for t in pts if t0 - 0.01 <= t <= t1 + 0.01)
        for a, b in zip(ts, ts[1:]):
            d = math.hypot(pts[b][0] - pts[a][0], pts[b][1] - pts[a][1])
            if d > 120:
                print(f"  {name}: {a:.1f} -> {b:.1f}: {d:.0f} px")
    print(f"\nFotogramas a revisar: {sorted(set(bad))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
