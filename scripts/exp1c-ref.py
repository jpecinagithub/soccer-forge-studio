#!/usr/bin/env python3
"""Experimento 1C: referencia temporal de la posicion del balon.

Construye data/clips/work/exp1c/ref-positions.csv (local, no en Git) a
partir de los puntos de visual_grounding (scripts/exp1c-grounding-
convert.py, SHEETS) y de la revision visual directa de las 26 hojas
ciegas (sin cajas) + 3 recortes ampliados x2 de los casos en disputa
(scripts/exp1c-zoom.py).

Metodo:
- 151 fotogramas a 5 fps (0,2 s) en los subtramos continuos sin cortes:
  S1 70.0-77.8 (40), S2b 134.6-141.8 (37), S3b 164.8-171.4 (34),
  S4 194.0-201.8 (40). Coordenadas en 1920x1080.
- Estado: V = balon visible (x,y = su centro), O = balon presente
  pero posicion no resoluble (ocluido / diminuto / mele), N = no hay
  balon en el fotograma (no ocurre en esta muestra).
- Los puntos de grounding se aceptan tal cual salvo correccion
  explicita tras lectura a plena resolucion (OVERRIDES).
- Los fotogramas O se excluyen de la evaluacion (ni acierto ni fallo);
  las cajas de los seguidores en ellos se registran como
  "no verificables", no como correctas ni como asociaciones erroneas.
- Las discrepancias >30 px con cajas TP verificadas en 1B se
  reexaminaron una a una: en 14 casos el TP 1B (casi siempre conf
  <=0.20, juzgado sobre hojas a 960 px) era el equivocado y la
  posicion 1C la corroboran grounding + lectura propia + continuidad
  de trayectoria. Se listan en NOTES.

Uso:
    python scripts/exp1c-ref.py
"""
import csv
import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "exp1c_grounding_convert",
    Path(__file__).resolve().parent / "exp1c-grounding-convert.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
SHEETS, to_orig = _mod.SHEETS, _mod.to_orig

OUT = Path("data/clips/work/exp1c/ref-positions.csv")

SEGMENTS = {"s1": (70.0, 77.8), "s2b": (134.6, 141.8),
            "s3b": (164.8, 171.4), "s4": (194.0, 201.8)}


def segment_of(t):
    for name, (a, b) in SEGMENTS.items():
        if a - 0.01 <= t <= b + 0.01:
            return name
    raise ValueError(f"t={t} fuera de los subtramos")


# (x, y) corregidos tras lectura a plena resolucion (recortes x2)
OVERRIDES = {
    74.2: (440, 460),   # grounding (374,498) caia 76 px a la izquierda,
                         # sobre el pie del jugador; balon visible en
                         # s1-f22.jpg a los pies del jugador rojo
    74.4: (450, 500),   # grounding (499,482) a 52 px; balon en s1-f23
                         # (recorte x2) a los pies del jugador amarillo
}

# Fotogramas O (posicion no resoluble; se excluyen de la evaluacion)
UNKNOWN = {
    70.8: "balon no distinguible a plena resolucion (label 1B '?'); "
          "punto de grounding sobre cesped vacio",
    169.4: "mele en el area, portero en el suelo; punto de grounding "
           "sobre cesped vacio (recorte x2)",
    169.6: "mele en el area, portero en el suelo; punto de grounding "
           "sobre el portero (recorte x2)",
    194.0: "balon diminuto en plano tactico amplio, no resoluble a "
           "plena resolucion; punto de grounding sobre cesped vacio "
           "(recorte x2)",
    194.2: "balon diminuto en plano tactico amplio, no resoluble a "
           "plena resolucion; punto de grounding sobre cesped vacio "
           "(recorte x2)",
    194.4: "balon diminuto en plano tactico amplio, no resoluble a "
           "plena resolucion; punto de grounding sobre cesped vacio "
           "(recorte x2)",
}

# Notas: correcciones, resoluciones de '?' de 1B, discrepancias con TP 1B
NOTES = {
    70.8: "O: " + UNKNOWN[70.8],
    74.2: "corregido a plena resolucion (440,460); grounding (374,498) "
          "caia 76 px a la izquierda, sobre el pie del jugador",
    74.4: "corregido a plena resolucion (450,500); grounding (499,482) "
          "a 52 px",
    74.0: "TP 1B (386,511)@0.39 a 42 px: balon en (428,508)",
    75.6: "TP 1B (424,468)@0.10 a 96 px: reexaminado, balon en "
          "(516,442); el TP 1B era un falso positivo probable",
    76.4: "TP 1B (795,538)@0.68 a 32 px: balon en (826,531)",
    77.2: "TP 1B (982,584)@0.54 a 32 px: balon en (1014,580)",
    134.6: "TP 1B (1405,746)@0.13 a 200 px: reexaminado, balon en "
           "(1306,573) a los pies de ESP 16; el TP 1B era un falso "
           "positivo",
    134.8: "TP 1B (1279,573)@0.66 a 31 px: balon en (1252,587)",
    135.2: "label 1B '?': balon visible a los pies de ESP 16",
    135.6: "TP 1B a 56 px (dos cajas 0.06-0.07): balon en (1440,631)",
    136.0: "TP 1B (1440,603)@0.52 a 77 px: reexaminado, balon en "
           "(1517,601)",
    136.8: "TP 1B (1451,565)@0.59 a 58 px: balon en (1509,559)",
    139.2: "TP 1B (1421,634)@0.12 a 172 px: reexaminado, balon en "
           "(1590,603)",
    140.8: "TP 1B (1451,609)@0.51 a 37 px: balon en (1488,615)",
    141.2: "label 1B '?': balon visible",
    164.8: "TP 1B (1072,644)@0.56 a 71 px: balon en (1142,636)",
    165.2: "TP 1B (990,521)@0.20 a 201 px: reexaminado, balon en "
           "(1150,643)",
    166.0: "TP 1B a 55 px: balon en (1148,641)",
    166.8: "TP 1B a 148 px (0.10/0.09): balon en (1140,601)",
    167.2: "TP 1B (1083,610)@0.09 a 108 px: balon en (1188,585)",
    167.6: "TP 1B (714,601)@0.05 a 527 px: balon en (1236,674)",
    168.0: "TP 1B (1383,651)@0.11 a 196 px: balon en (1187,655)",
    169.4: "O: " + UNKNOWN[169.4],
    169.6: "O: " + UNKNOWN[169.6],
    170.4: "TP 1B (1396,652)@0.53 a 57 px: balon en (1452,641)",
    170.8: "label 1B '?': balon visible a los pies del jugador amarillo",
    171.2: "TP 1B (1396,664)@0.80 a 39 px: balon en (1357,669)",
    194.0: "O: " + UNKNOWN[194.0],
    194.2: "O: " + UNKNOWN[194.2],
    194.4: "O: " + UNKNOWN[194.4],
    194.6: "zoom rapido de camara entre 194.4 y 194.6 (salto de 385 px "
           "en coords de imagen; el balon no se movio tanto)",
    198.4: "TP 1B (1305,605)@0.12 a 348 px: reexaminado, balon en "
           "(1081,872)",
    198.8: "TP 1B (1110,851)@0.53 a 51 px: balon en (1071,818)",
    199.2: "TP 1B (1134,733)@0.56 a 131 px: reexaminado, balon en "
           "(1263,711)",
    200.0: "TP 1B (1408,657)@0.17 a 263 px: reexaminado, balon en "
           "(1146,636)",
    200.4: "TP 1B (1435,666)@0.27 a 292 px: reexaminado, balon en "
           "(1148,613)",
    200.6: "pase a la derecha; salto de 217 px desde 200.4 (real)",
    201.6: "TP 1B (1507,676)@0.29 a 163 px: reexaminado, balon en "
           "(1367,594)",
}


def main() -> int:
    pts = {}
    for sheet, cells in SHEETS.items():
        for t, xn, yn in cells:
            pts[round(t, 1)] = to_orig(xn, yn)
    assert len(pts) == 151, f"esperaba 151 puntos, hay {len(pts)}"

    rows = []
    for t in sorted(pts):
        seg = segment_of(t)
        if t in UNKNOWN:
            rows.append({"t_abs": f"{t:.1f}", "segment": seg, "status": "O",
                         "x": "", "y": "", "note": NOTES[t]})
        else:
            x, y = OVERRIDES.get(t, pts[t])
            rows.append({"t_abs": f"{t:.1f}", "segment": seg, "status": "V",
                         "x": x, "y": y, "note": NOTES.get(t, "")})

    # Continuidad: 0,2 s entre fotogramas consecutivos del mismo subtramo
    for name, (a, b) in SEGMENTS.items():
        ts = [float(r["t_abs"]) for r in rows if r["segment"] == name]
        assert len(ts) == round((b - a) / 0.2) + 1, (name, len(ts))
        for u, v in zip(ts, ts[1:]):
            assert abs(v - u - 0.2) < 1e-6, (name, u, v)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["t_abs", "segment", "status",
                                           "x", "y", "note"])
        w.writeheader()
        w.writerows(rows)

    n_v = sum(1 for r in rows if r["status"] == "V")
    n_o = sum(1 for r in rows if r["status"] == "O")
    print(f"Referencia escrita: {OUT} ({len(rows)} fotogramas, "
          f"V={n_v}, O={n_o}, N=0)")
    print(f"  O: {sorted(UNKNOWN)}")
    print(f"  Overrides: {sorted(OVERRIDES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
