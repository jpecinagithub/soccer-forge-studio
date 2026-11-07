#!/usr/bin/env python3
"""Comparación clip completo: detecciones crudas P640-FULL vs salida
de seguimiento E1-C (Experimento 1B, paso 1 en el clip completo).

Ambos sobre el clip B1 completo (5.931 fotogramas), mismo yolov8s,
imgsz 640. P640-FULL: predict conf 0.05 (barrido post-hoc a 0.25).
E1-C: track ByteTrack conf 0.25 (informe exp1).
Los segmentos field-view / close-up / replay son de la anotación v2
(exploratoria; sus límites tienen precisión +-1 s).

Uso: python scripts/exp1b-fullclip.py
"""

import json

FULL = "docs/decisions/exp1b/pred640-full.json"
E1C = "docs/decisions/exp1/full-b1.json"
ANN = "docs/evaluation/B1-georgia-espana-annotation.json"


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def ball(frames, min_conf=0.0):
    return [(f, [d for d in f["detections"]
                 if d["cls"] == "sports ball" and d["conf"] >= min_conf])
            for f in frames]


def summarize(name, frames_with_ball, total_frames):
    n_fw = sum(1 for _, b in frames_with_ball if b)
    n_det = sum(len(b) for _, b in frames_with_ball)
    print(f"  {name}: {n_fw}/{total_frames} fotogramas con balón "
          f"({100*n_fw/max(1, total_frames):.1f}%), {n_det} detecciones")
    return n_fw, n_det


def main() -> int:
    full = load(FULL)["frames"]
    e1c = load(E1C)["frames"]
    assert len(full) == len(e1c) == 5931, (len(full), len(e1c))
    ann = load(ANN)
    segs = ann["segments"]
    fv = [(s["tStart"], s["tEnd"]) for s in segs if s["type"] == "field-view"]
    cu = [(s["tStart"], s["tEnd"]) for s in segs if s["type"] == "close-up"]
    rp = [(s["tStart"], s["tEnd"]) for s in segs if s["type"] == "replay"]

    def in_segs(t, lst):
        return any(a <= t < b for a, b in lst)

    print("== Clip completo (5.931 fotogramas) ==")
    summarize("P640-FULL @0.05", ball(full, 0.05), 5931)
    fw25, det25 = summarize("P640-FULL @0.25", ball(full, 0.25), 5931)
    fw_tr, det_tr = summarize("E1-C track @0.25", ball(e1c, 0.0), 5931)
    print(f"  -> A igual confianza (0.25), el seguidor conserva "
          f"{det_tr}/{det25} detecciones ({100*det_tr/max(1, det25):.1f}%) "
          f"y {fw_tr}/{fw25} fotogramas ({100*fw_tr/max(1, fw25):.1f}%).")

    print("\n== Solo vista de campo (anotación v2: "
          f"{sum(b-a for a, b in fv):.0f} s en {len(fv)} segmentos) ==")
    fv_frames_full = [f for f in full if in_segs(f["t_abs"], fv)]
    fv_frames_e1c = [f for f in e1c if in_segs(f["t_abs"], fv)]
    n = len(fv_frames_full)
    summarize("P640-FULL @0.05", ball(fv_frames_full, 0.05), n)
    fw25, det25 = summarize("P640-FULL @0.25", ball(fv_frames_full, 0.25), n)
    fw_tr, det_tr = summarize("E1-C track @0.25", ball(fv_frames_e1c, 0.0), n)
    print(f"  -> En vista de campo, a igual confianza el seguidor conserva "
          f"{det_tr}/{det25} detecciones ({100*det_tr/max(1, det25):.1f}%) "
          f"y {fw_tr}/{fw25} fotogramas ({100*fw_tr/max(1, fw25):.1f}%).")

    print("\n== Primeros planos y repeticiones (contexto) ==")
    for label, lst in [("close-up", cu), ("replay", rp)]:
        sub_full = [f for f in full if in_segs(f["t_abs"], lst)]
        sub_e1c = [f for f in e1c if in_segs(f["t_abs"], lst)]
        print(f"  {label} ({sum(b-a for a, b in lst):.0f} s, {len(sub_full)} fotogramas):")
        summarize("  P640-FULL @0.05", ball(sub_full, 0.05), len(sub_full))
        summarize("  P640-FULL @0.25", ball(sub_full, 0.25), len(sub_full))
        summarize("  E1-C track @0.25", ball(sub_e1c, 0.0), len(sub_e1c))

    print("\n== Balón en el golpeo de los 5 tiros puntuables ==")
    scored = ann["scoring"]["scoredEvents"]
    events = {}
    for play in ann["plays"]:
        for ev in play["events"]:
            events[ev["id"]] = ev
    for ev_id in scored:
        ev = events[ev_id]
        t0, t1 = ev["tStart"], ev["tEnd"]
        # ventana +-0,5 s alrededor del inicio del evento
        win_full = [f for f in full if t0 - 0.5 <= f["t_abs"] <= t0 + 0.5]
        win_e1c = [f for f in e1c if t0 - 0.5 <= f["t_abs"] <= t0 + 0.5]
        n05 = sum(1 for f in win_full
                  if any(d["cls"] == "sports ball" and d["conf"] >= 0.05
                         for d in f["detections"]))
        n25 = sum(1 for f in win_full
                  if any(d["cls"] == "sports ball" and d["conf"] >= 0.25
                         for d in f["detections"]))
        ntr = sum(1 for f in win_e1c
                  if any(d["cls"] == "sports ball" for d in f["detections"]))
        print(f"  {ev_id} ({ev['type']}, t={t0}-{t1}s): "
              f"P640-FULL@0.05 {n05}/{len(win_full)} fotogramas, "
              f"@0.25 {n25}/{len(win_full)}, E1-C track {ntr}/{len(win_e1c)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
