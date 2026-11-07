#!/usr/bin/env python3
"""Experimento 1B — Detecciones crudas YOLO (sin seguidor).

Recorre un vídeo con `model.predict` y guarda TODAS las cajas por
fotograma (clase, bbox, confianza), sin track id. El umbral de
confianza se deja bajo (por defecto 0.05) para que el barrido de
umbrales del balón pueda hacerse post-hoc sobre las detecciones
guardadas, sin re-ejecutar la inferencia.

NO infiere pases, tiros ni ningún evento: solo detección cruda.

Uso:
    python scripts/exp1b-predict.py --video VIDEO --offset 62.0 \
        --weights yolov8s.pt --imgsz 640 --conf 0.05 \
        --out docs/decisions/exp1b/pred640-s1.json
"""

import argparse
import json
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
    p.add_argument("--conf", type=float, default=0.05,
                   help="Umbral de confianza (bajo: guardar para barrido post-hoc)")
    p.add_argument("--iou", type=float, default=0.5, help="Umbral IoU (NMS)")
    p.add_argument("--imgsz", type=int, default=640, help="Tamaño de inferencia")
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
    results = model.predict(
        source=args.video,
        classes=classes,
        conf=args.conf,
        iou=args.iou,
        imgsz=args.imgsz,
        verbose=False,
        stream=True,
    )

    frames = []
    for idx, res in enumerate(results):
        dets = []
        boxes = res.boxes
        if boxes is not None and len(boxes) > 0:
            xyxy = boxes.xyxy.tolist()
            confs = boxes.conf.tolist()
            clss = boxes.cls.tolist()
            for box, conf, cls in zip(xyxy, confs, clss):
                dets.append({
                    "cls": CLASS_NAMES.get(int(cls), f"class_{int(cls)}"),
                    "bbox": [round(float(v), 1) for v in box],
                    "conf": round(float(conf), 3),
                })
        frames.append({
            "frame": idx,
            "t_rel": round(idx / fps, 3) if fps else idx,
            "t_abs": round(args.offset + idx / fps, 3) if fps else idx,
            "detections": dets,
        })
    wall = time.perf_counter() - t0
    n_frames = len(frames)

    per_class: dict[str, dict] = {}
    for cls_name in CLASS_NAMES.values():
        dets_cls = [d for f in frames for d in f["detections"] if d["cls"] == cls_name]
        frames_with = sum(1 for f in frames
                          if any(d["cls"] == cls_name for d in f["detections"]))
        per_class[cls_name] = {
            "detections": len(dets_cls),
            "mean_per_frame": round(len(dets_cls) / n_frames, 3) if n_frames else 0,
            "frames_with_at_least_one": frames_with,
            "fraction_frames": round(frames_with / n_frames, 4) if n_frames else 0,
        }

    out = {
        "config": {
            "weights": args.weights,
            "ultralytics": ultralytics.__version__,
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "mode": "predict",
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
              f"frames_with={st['fraction_frames']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
