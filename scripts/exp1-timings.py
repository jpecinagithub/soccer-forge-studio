#!/usr/bin/env python3
"""Descomposición de tiempos del Experimento 1 (fragmento 35-65 s).

Mide por separado, sobre el mismo fragmento y configuración:
  A. decodificación de vídeo (lectura de fotogramas con cv2, sin modelo)
  B. inferencia sin seguimiento (YOLO predict, incluye decodificación)
  C. inferencia + seguimiento (YOLO track, incluye decodificación)
De ahí: inferencia ≈ B - A; seguimiento ≈ C - B.
También informa la memoria máxima (ru_maxrss) del proceso.

Uso:
    python scripts/exp1-timings.py --video VIDEO --weights yolov8s.pt
"""

import argparse
import resource
import time

import cv2
from ultralytics import YOLO


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video", required=True)
    p.add_argument("--weights", default="yolov8s.pt")
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--iou", type=float, default=0.5)
    p.add_argument("--imgsz", type=int, default=640)
    args = p.parse_args()

    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    n_expected = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    # A. Solo decodificación
    t0 = time.perf_counter()
    cap = cv2.VideoCapture(args.video)
    n = 0
    while True:
        ok, _ = cap.read()
        if not ok:
            break
        n += 1
    cap.release()
    t_decode = time.perf_counter() - t0

    # B. Inferencia sin seguimiento
    model = YOLO(args.weights)
    t0 = time.perf_counter()
    n_det = 0
    for res in model.predict(source=args.video, classes=[0, 32],
                             conf=args.conf, iou=args.iou, imgsz=args.imgsz,
                             verbose=False, stream=True):
        n_det += len(res.boxes) if res.boxes is not None else 0
    t_predict = time.perf_counter() - t0

    # C. Inferencia + seguimiento ByteTrack
    t0 = time.perf_counter()
    n_det_t = 0
    for res in model.track(source=args.video, tracker="bytetrack.yaml",
                           classes=[0, 32], conf=args.conf, iou=args.iou,
                           imgsz=args.imgsz, persist=True,
                           verbose=False, stream=True):
        n_det_t += len(res.boxes) if res.boxes is not None else 0
    t_track = time.perf_counter() - t0

    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(f"frames={n_expected} fps_video={fps}")
    print(f"A decode_only: {t_decode:.1f}s ({n} frames)")
    print(f"B predict (decode+infer): {t_predict:.1f}s det={n_det}")
    print(f"C track (decode+infer+track): {t_track:.1f}s det={n_det_t}")
    print(f"inferencia estimada (B-A): {t_predict - t_decode:.1f}s")
    print(f"seguimiento estimado (C-B): {t_track - t_predict:.1f}s")
    print(f"max_rss: {rss_mb:.0f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
