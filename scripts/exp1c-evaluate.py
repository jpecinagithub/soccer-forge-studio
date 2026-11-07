#!/usr/bin/env python3
"""Experimento 1C: evaluacion de los seguidores contra la referencia
temporal del balon (ref-positions.csv, 5 fps).

Metodos evaluados (todos sobre las MISMAS detecciones P1280 guardadas):
- P1280-raw@0.05 / @0.25: detecciones crudas (techo del detector).
- T1280: ByteTrack por defecto, conf 0.25, clases person+ball (1B).
- BT-ball: ByteTrack solo-balon (varias configuraciones).
- Linker: enlazador temporal propio (varias configuraciones).

Metricas por fotograma V de referencia (tolerancia 50 px por defecto;
sensibilidad a 25 y 100 px):
- recall: fotogramas V con >=1 posicion OBSERVADA a <=tol del balon.
- asociaciones a objetos equivocados: posiciones observadas a >tol del
  balon en fotogramas V (y fotogramas V con >=1).
- fragmentacion: nº de IDs distintos que cubren el balon, nº de cambios
  de ID entre fotogramas V cubiertos consecutivos, longitud media de
  racha (en fotogramas V).
- huecos: racha maxima de fotogramas V consecutivos sin cobertura.
- ESTIMADO: posiciones predichas en oclusion NO cuentan en recall;
  se registra aparte (fotogramas V cubiertos SOLO por estimado).
- Fotogramas O: las cajas se registran como no verificables.

Uso:
    python scripts/exp1c-evaluate.py
Escribe docs/decisions/exp1c/evaluation.json e imprime la tabla.
"""
import csv
import json
import math
from pathlib import Path

BASE = Path("docs/decisions/exp1b")
OUT = Path("docs/decisions/exp1c")
REF = Path("data/clips/work/exp1c/ref-positions.csv")
TOLS = (25, 50, 100)
TUNE_SEGS = ("s1", "s2b")
TEST_SEGS = ("s3b", "s4")


def load_ref():
    rows = []
    with open(REF, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "t": float(r["t_abs"]), "seg": r["segment"],
                "status": r["status"],
                "x": float(r["x"]) if r["x"] else None,
                "y": float(r["y"]) if r["y"] else None})
    return rows


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def positions_from_frames(frames, t, kind):
    """Posiciones (track_id, cx, cy, status) de un metodo en t_abs."""
    for f in frames:
        if abs(f["t_abs"] - t) < 0.02:
            if kind == "track":  # T1280: detections con track_id
                out = []
                for d in f["detections"]:
                    if d["cls"] == "sports ball" and d.get("track_id") is not None:
                        x0, y0, x1, y1 = d["bbox"]
                        out.append((d["track_id"], (x0 + x1) / 2,
                                    (y0 + y1) / 2, "observed"))
                return out
            if kind == "pred":  # P1280 crudo: detecciones, sin track
                out = []
                for d in f["detections"]:
                    if d["cls"] == "sports ball":
                        x0, y0, x1, y1 = d["bbox"]
                        out.append((None, (x0 + x1) / 2, (y0 + y1) / 2,
                                    "observed"))
                return out
            # bt-ball / linker: tracks con status
            out = []
            for tr in f["tracks"]:
                x0, y0, x1, y1 = tr["bbox"]
                out.append((tr["track_id"], (x0 + x1) / 2, (y0 + y1) / 2,
                            tr.get("status", "observed")))
            return out
    return []


def evaluate(method_name, frames_by_seg, kind, min_conf=None):
    ref = load_ref()
    # min_conf solo para P1280 crudo
    per_seg = {}
    for seg in ("s1", "s2b", "s3b", "s4"):
        rows = [r for r in ref if r["seg"] == seg]
        v_rows = [r for r in rows if r["status"] == "V"]
        o_rows = [r for r in rows if r["status"] == "O"]
        frames = frames_by_seg[seg]
        cover = {}  # tol -> nº V cubiertos
        for tol in TOLS:
            cover[tol] = 0
        cover_ids = []      # id que cubre cada V (None si no cubre)
        covered_flags = []  # True si el V esta cubierto (para huecos)
        wrong_frames = 0
        wrong_tracks = 0
        est_only = 0
        o_with_tracks = 0
        o_tracks = 0
        for r in rows:
            pos = positions_from_frames(frames, r["t"], kind)
            if min_conf is not None:
                # filtrar por conf de deteccion (solo P1280 crudo)
                pos = [p for p, f in zip(pos, _dets_at(frames, r["t"]))
                       if f["conf"] >= min_conf]
            if r["status"] == "O":
                if pos:
                    o_with_tracks += 1
                    o_tracks += len(pos)
                continue
            obs = [p for p in pos if p[3] == "observed"]
            est = [p for p in pos if p[3] == "estimated"]
            dists = [(math.hypot(p[1] - r["x"], p[2] - r["y"]), p[0])
                     for p in obs]
            good = [d for d in dists if d[0] <= 50]
            for tol in TOLS:
                if any(d[0] <= tol for d in dists):
                    cover[tol] += 1
            # covered: booleano (para huecos); cover_id: id (para
            # fragmentacion; en crudo no hay id -> 0 si cubre)
            covered_flags.append(bool(good))
            cover_ids.append(good[0][1] if good else None)
            if kind == "pred" and good:
                cover_ids[-1] = 0
            wrong = [d for d in dists if d[0] > 50]
            if wrong:
                wrong_frames += 1
                wrong_tracks += len(wrong)
            if not good and est:
                est_only += 1
        # fragmentacion y huecos sobre fotogramas V cubiertos
        ids = [i for i in cover_ids if i is not None]
        switches = sum(1 for a, b in zip(ids, ids[1:]) if a != b)
        runs, cur, cur_id = [], 0, None
        for i in cover_ids:
            if i is not None and i == cur_id:
                cur += 1
            else:
                if cur:
                    runs.append(cur)
                cur = 1 if i is not None else 0
                cur_id = i
        if cur:
            runs.append(cur)
        max_gap, gap = 0, 0
        for c in covered_flags:
            gap = gap + 1 if not c else 0
            max_gap = max(max_gap, gap)
        n_v = len(v_rows)
        per_seg[seg] = {
            "n_V": n_v, "n_O": len(o_rows),
            "recall": {str(tol): round(cover[tol] / n_v, 3) for tol in TOLS},
            "covered_50": cover[50],
            "wrong_frames": wrong_frames,
            "wrong_rate": round(wrong_frames / n_v, 3),
            "wrong_tracks": wrong_tracks,
            "est_only_frames": est_only,
            "distinct_cover_ids": len(set(ids)),
            "id_switches": switches,
            "mean_run_Vframes": round(sum(runs) / len(runs), 2) if runs else 0,
            "max_gap_Vframes": max_gap,
            "max_gap_s": round(max_gap * 0.2, 1),
            "O_frames_with_tracks": o_with_tracks,
            "O_tracks": o_tracks,
        }
    return {"method": method_name, "per_seg": per_seg}


def _dets_at(frames, t):
    for f in frames:
        if abs(f["t_abs"] - t) < 0.02:
            return [d for d in f["detections"] if d["cls"] == "sports ball"]
    return []


def aggregate(ev):
    def agg(segs):
        n_v = sum(ev["per_seg"][s]["n_V"] for s in segs)
        cov = sum(ev["per_seg"][s]["covered_50"] for s in segs)
        out = {"n_V": n_v, "recall_50": round(cov / n_v, 3) if n_v else 0}
        for tol in ("25", "100"):
            c = sum(round(ev["per_seg"][s]["recall"][tol]
                          * ev["per_seg"][s]["n_V"]) for s in segs)
            out[f"recall_{tol}"] = round(c / n_v, 3) if n_v else 0
        out["wrong_rate"] = round(
            sum(ev["per_seg"][s]["wrong_frames"] for s in segs) / n_v, 3)
        out["wrong_tracks"] = sum(ev["per_seg"][s]["wrong_tracks"]
                                  for s in segs)
        out["est_only"] = sum(ev["per_seg"][s]["est_only_frames"]
                              for s in segs)
        out["distinct_ids"] = sum(ev["per_seg"][s]["distinct_cover_ids"]
                                  for s in segs)
        out["switches"] = sum(ev["per_seg"][s]["id_switches"] for s in segs)
        out["max_gap_s"] = max(ev["per_seg"][s]["max_gap_s"] for s in segs)
        return out
    return {"tune_S1S2": agg(TUNE_SEGS), "test_S3S4": agg(TEST_SEGS),
            "all": agg(("s1", "s2b", "s3b", "s4"))}


def main() -> int:
    ref = load_ref()
    segs = {"s1": "s1", "s2b": "s2", "s3b": "s3", "s4": "s4"}
    # Cargar frames por subtramo para cada familia
    pred, track = {}, {}
    for seg, s in segs.items():
        pred[seg] = load_json(BASE / f"pred1280-{s}.json")["frames"]
        track[seg] = load_json(BASE / f"track1280-{s}.json")["frames"]

    methods = []  # (nombre, kind, {seg: frames}, min_conf)
    methods.append(("P1280-raw@0.05", "pred", pred, 0.05))
    methods.append(("P1280-raw@0.25", "pred", pred, 0.25))
    methods.append(("T1280 (ref, BT por defecto conf 0.25)",
                    "track", track, None))

    # BT-ball y linker: agrupar por configuracion (el fichero es 1 tramo).
    # OJO: el config.segment es s1..s4 pero la referencia usa s2b/s3b
    # para los subtramos sin cortes.
    segmap = {"s1": "s1", "s2": "s2b", "s3": "s3b", "s4": "s4"}
    grouped = {}
    for path in sorted(OUT.glob("bt-ball-*.json")):
        d = load_json(path)
        seg = segmap[d["config"]["segment"]]
        tag = path.stem.replace("bt-ball-", "")
        cfg = tag.split("-", 1)[1]  # quita el prefijo s1/s2
        grouped.setdefault(f"BT-ball {cfg}", {})[seg] = d["frames"]
    for path in sorted(OUT.glob("link-*.json")):
        d = load_json(path)
        seg = segmap[d["config"]["segment"]]
        tag = path.stem.replace("link-", "")
        cfg = tag.split("-", 1)[1]
        grouped.setdefault(f"Linker {cfg}", {})[seg] = d["frames"]
    for name, frames_by_seg in grouped.items():
        kind = "bt"
        methods.append((name, kind, frames_by_seg, None))

    results = []
    for name, kind, frames_by_seg, mc in methods:
        frames_full = {seg: frames_by_seg.get(seg, []) for seg in
                       ("s1", "s2b", "s3b", "s4")}
        ev = evaluate(name, frames_full, kind, mc)
        ev["agg"] = aggregate(ev)
        ev["segments_run"] = sorted(frames_by_seg.keys())
        results.append(ev)

    with open(OUT / "evaluation.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, ensure_ascii=False)

    def fmt(a):
        return (f"{a['recall_50']:.3f} {a['wrong_rate']:.2f} "
                f"{a['distinct_ids']:3d} {a['switches']:3d} {a['max_gap_s']:4.1f}")

    print(f"{'Metodo':42} {'TUNE S1+S2':>28} {'TEST S3+S4':>28}")
    print(f"{'':42} {'rec50 wrong ids sw gap':>28} "
          f"{'rec50 wrong ids sw gap':>28}")
    for ev in results:
        t, s = ev["agg"]["tune_S1S2"], ev["agg"]["test_S3S4"]
        ran_test = any(x in ev["segments_run"] for x in ("s3b", "s4"))
        test_str = fmt(s) if ran_test else "— no ejecutado en S3+S4 —"
        print(f"{ev['method'][:42]:42} {fmt(t):>28} {test_str:>28}")
    print("\nrec50=recall@50px, wrong=tasa de fotogramas V con >=1 track "
          "equivocado, ids=IDs distintos que cubren, sw=cambios de ID, "
          "gap=hueco max (s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
