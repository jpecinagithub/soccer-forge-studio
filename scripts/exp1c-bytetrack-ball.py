#!/usr/bin/env python3
"""Experimento 1C: ByteTrack configurado para balon sobre detecciones
P1280 ya guardadas (SIN repetir inferencia).

Alimenta EXACTAMENTE las mismas detecciones crudas a 1280 (conf >= 0.05)
que 1B, pero SOLO la clase balon y con umbrales de track propios:
detecciones fuertes (>= high) para iniciar, debiles (>= low) solo para
continuar en la segunda asociacion de ByteTrack. Reinicia en los cortes
manuales (lista explicita; ayuda experimental, no automatizada).

Referencia de comparacion (T1280, 1B): model.track() con conf 0.25,
clases person+ball, bytetrack.yaml por defecto (high 0.25, low 0.1,
new 0.25, buffer 30, match 0.8, fuse True).

Uso (en Oracle, venv con ultralytics 8.4.204):
    python exp1c-bytetrack-ball.py --pred exp1b/pred1280-s1.json \\
        --seg s1 --out exp1c/bt-ball-s1-b30-m08.json \\
        --high 0.25 --low 0.05 --new 0.25 --buffer 30 --match 0.8
    python exp1c-bytetrack-ball.py --pred exp1b/pred1280-s2.json \\
        --seg s2 --out exp1c/bt-ball-s2-b30-m08.json --reset-at 134.6
"""
import argparse
import json
import time
from types import SimpleNamespace

import numpy as np
from ultralytics.engine.results import Boxes
from ultralytics.trackers.byte_tracker import BYTETracker

ORIG_SHAPE = (1080, 1920)  # (alto, ancho) del clip B1


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pred", required=True, help="JSON pred1280 del tramo")
    p.add_argument("--seg", required=True, help="s1|s2|s3|s4")
    p.add_argument("--out", required=True, help="JSON de salida")
    p.add_argument("--high", type=float, default=0.25,
                   help="track_high_thresh: fuerte para iniciar")
    p.add_argument("--low", type=float, default=0.05,
                   help="track_low_thresh: debil para continuar")
    p.add_argument("--new", type=float, default=0.25,
                   help="new_track_thresh")
    p.add_argument("--buffer", type=int, default=30,
                   help="track_buffer (fotogramas que sobrevive un track perdido)")
    p.add_argument("--match", type=float, default=0.8,
                   help="match_thresh (similitud de asociacion)")
    p.add_argument("--fuse", type=int, default=1, choices=[0, 1],
                   help="fuse_score")
    p.add_argument("--reset-at", default="",
                   help="t_abs de cortes (coma) donde reiniciar el seguidor")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    with open(args.pred, encoding="utf-8") as fh:
        data = json.load(fh)
    frames = data["frames"]
    resets = [float(x) for x in args.reset_at.split(",") if x.strip()]

    cfg = {
        "method": "bytetrack-ball",
        "tracker": "ultralytics BYTETracker 8.4.204",
        "input": args.pred,
        "segment": args.seg,
        "classes_fed": ["sports ball"],
        "min_conf_fed": 0.05,
        "track_high_thresh": args.high,
        "track_low_thresh": args.low,
        "new_track_thresh": args.new,
        "track_buffer": args.buffer,
        "match_thresh": args.match,
        "fuse_score": bool(args.fuse),
        "resets_at_t_abs": resets,
        "note": "cortes manuales: ayuda experimental, no automatizada",
    }
    tracker = BYTETracker(SimpleNamespace(**{
        k: v for k, v in cfg.items()
        if k in ("track_high_thresh", "track_low_thresh", "new_track_thresh",
                 "track_buffer", "match_thresh", "fuse_score")}))

    out_frames = []
    t0 = time.perf_counter()
    for fr in frames:
        t = fr["t_abs"]
        if any(abs(t - r) < 0.02 for r in resets):
            tracker.reset()
        balls = [d for d in fr["detections"]
                 if d["cls"] == "sports ball" and d["conf"] >= 0.05]
        if balls:
            arr = np.array([[*d["bbox"], d["conf"], 32.0] for d in balls],
                           dtype=np.float32)
        else:
            arr = np.zeros((0, 6), dtype=np.float32)
        out = tracker.update(Boxes(arr, ORIG_SHAPE))
        tracks = []
        for row in out:
            x1, y1, x2, y2, tid, score, _cls, idx = row
            det = balls[int(idx)] if 0 <= int(idx) < len(balls) else None
            tracks.append({
                "track_id": int(tid),
                "bbox": [round(float(v), 1) for v in (x1, y1, x2, y2)],
                "conf": round(float(score), 3),
                "det_conf": round(float(det["conf"]), 3) if det else None,
                "det_bbox": det["bbox"] if det else None,
            })
        out_frames.append({"frame": fr["frame"], "t_abs": t,
                           "tracks": tracks})
    wall = time.perf_counter() - t0

    n_tracks = len({tr["track_id"] for f in out_frames for tr in f["tracks"]})
    result = {"config": cfg, "video": data.get("video"),
              "n_frames": len(out_frames), "n_tracks": n_tracks,
              "wall_s": round(wall, 3),
              "frames": out_frames}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh)
    print(f"{args.seg}: {len(out_frames)} fotogramas, {n_tracks} tracks, "
          f"{wall:.2f} s -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
