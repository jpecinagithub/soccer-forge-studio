#!/usr/bin/env python3
"""Experimento 1 — Visión local YOLO + ByteTrack (Soccer Forge Studio).

Recorre un vídeo con seguimiento y guarda predicciones en JSON:
por fotograma, detecciones (clase, bbox, confianza, track id);
visibilidad del balón por fotograma; estadísticas de tracks;
tiempo de ejecución y FPS de proceso.

NO infiere pases, tiros ni ningún evento: solo detección,
seguimiento y visibilidad del balón.

Uso:
    python scripts/exp1-track.py --video VIDEO --offset 35.0 \
        --weights yolov8s.pt --out docs/decisions/exp1/frag-35-65.json
"""

import argparse
import json
import statistics
import time

import cv2
import torch
import ultralytics
from ultralytics import YOLO

CLASS_NAMES = {0: "person", 32: "sports ball"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video", required=True, help="Vídeo de entrada")
    p.add_argument("--offset", type=float, default=0.0,
                   help="Desplazamiento en segundos respecto al clip original")
    p.add_argument("--weights", default="yolov8s.pt", help="Pesos YOLO")
    p.add_argument("--conf", type=float, default=0.25, help="Umbral de confianza")
    p.add_argument("--iou", type=float, default=0.5, help="Umbral IoU (NMS)")
    p.add_argument("--imgsz", type=int, default=640, help="Tamaño de inferencia")
    p.add_argument("--tracker", default="bytetrack.yaml", help="Config del seguidor")
    p.add_argument("--classes", default="0,32",
                   help="Clases COCO a detectar (person=0, sports ball=32)")
    p.add_argument("--out", required=True, help="JSON de salida")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    classes = [int(c) for c in args.classes.split(",") if c != ""]

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"No se puede abrir el vídeo: {args.video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    n_frames_expected = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    duration = n_frames_expected / fps if fps else 0.0

    model = YOLO(args.weights)
    t0 = time.perf_counter()
    results = model.track(
        source=args.video,
        tracker=args.tracker,
        classes=classes,
        conf=args.conf,
        iou=args.iou,
        imgsz=args.imgsz,
        persist=True,
        verbose=False,
        stream=True,
    )

    frames = []
    track_lengths: dict[tuple[str, int], int] = {}
    n_no_id = 0
    for idx, res in enumerate(results):
        dets = []
        boxes = res.boxes
        if boxes is not None and len(boxes) > 0:
            xyxy = boxes.xyxy.tolist()
            confs = boxes.conf.tolist()
            clss = boxes.cls.tolist()
            ids = boxes.id.tolist() if boxes.id is not None else [None] * len(boxes)
            for box, conf, cls, tid in zip(xyxy, confs, clss, ids):
                name = CLASS_NAMES.get(int(cls), f"class_{int(cls)}")
                track_id = int(tid) if tid is not None else None
                if track_id is None:
                    n_no_id += 1
                else:
                    key = (name, track_id)
                    track_lengths[key] = track_lengths.get(key, 0) + 1
                dets.append({
                    "cls": name,
                    "bbox": [round(float(v), 1) for v in box],
                    "conf": round(float(conf), 3),
                    "track_id": track_id,
                })
        frames.append({
            "frame": idx,
            "t_rel": round(idx / fps, 3) if fps else idx,
            "t_abs": round(args.offset + idx / fps, 3) if fps else idx,
            "detections": dets,
        })
    wall = time.perf_counter() - t0
    n_frames = len(frames)

    # Estadísticas por clase
    per_class: dict[str, dict] = {}
    for cls_name in CLASS_NAMES.values():
        dets_cls = [d for f in frames for d in f["detections"] if d["cls"] == cls_name]
        lengths = [n for (c, _), n in track_lengths.items() if c == cls_name]
        frames_with = sum(1 for f in frames
                          if any(d["cls"] == cls_name for d in f["detections"]))
        per_class[cls_name] = {
            "detections": len(dets_cls),
            "mean_per_frame": round(len(dets_cls) / n_frames, 3) if n_frames else 0,
            "frames_with_at_least_one": frames_with,
            "fraction_frames": round(frames_with / n_frames, 4) if n_frames else 0,
            "n_tracks": len(lengths),
            "mean_track_length_frames": round(statistics.mean(lengths), 2) if lengths else 0,
            "median_track_length_frames": statistics.median(lengths) if lengths else 0,
            "max_track_length_frames": max(lengths) if lengths else 0,
            "single_frame_tracks": sum(1 for n in lengths if n == 1),
        }

    out = {
        "config": {
            "weights": args.weights,
            "ultralytics": ultralytics.__version__,
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "tracker": args.tracker,
            "conf": args.conf,
            "iou": args.iou,
            "imgsz": args.imgsz,
            "classes": classes,
            "offset_seconds": args.offset,
        },
        "video": {
            "path": args.video,
            "fps": fps,
            "frames_expected": n_frames_expected,
            "frames_processed": n_frames,
            "duration_seconds": round(duration, 3),
            "width": width,
            "height": height,
        },
        "stats": {
            "wall_seconds": round(wall, 1),
            "processing_fps": round(n_frames / wall, 2) if wall else 0,
            "realtime_factor": round(wall / duration, 2) if duration else 0,
            "detections_without_track_id": n_no_id,
            "per_class": per_class,
        },
        "frames": frames,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print(f"frames={n_frames} wall={wall:.1f}s fps={n_frames / wall:.2f} "
          f"realtime_x{wall / duration:.2f}")
    for cls_name, st in per_class.items():
        print(f"{cls_name}: det/frame={st['mean_per_frame']} "
              f"frames_with={st['fraction_frames']:.3f} "
              f"tracks={st['n_tracks']} mean_len={st['mean_track_length_frames']}f")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
