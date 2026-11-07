#!/usr/bin/env python3
"""Experimento 1C: enlazador temporal sencillo para el balon.

Vecino mas cercano con prediccion de movimiento (filtro de Kalman de
velocidad constante) sobre las detecciones P1280 ya guardadas (SIN
repetir inferencia). Reglas:

- Inicio: deteccion fuerte (conf >= 0.25) confirmada por una segunda
  deteccion coherente en el fotograma siguiente.
- Continuacion: detecciones debiles (conf >= 0.05) SOLO si caen dentro
  de la puerta alrededor de la posicion predicha y con coherencia de
  velocidad (sin aceptar cualquier punto cercano).
- Puerta: radio = min(gate_max, gate_min + gate_k * |v|), con |v| en
  px/fotograma a 25 fps; si |v| > 25 px/fotograma, el desplazamiento
  desde la ultima posicion observada debe apuntar a menos de 72 grados
  de la velocidad (cos > 0.3).
- Oclusion: si no hay deteccion, el track sigue prediciendo hasta
  coast_max fotogramas; esas posiciones figuran como ESTIMADAS (nunca
  como deteccion observada ni como mejora de recuperacion) y despues
  el track termina.
- Cortes: reinicio total (tracks activos + pendientes) en los t_abs
  de la lista manual (ayuda experimental, no automatizada).

El filtro de Kalman es fijo (no se ajusta): Q con ruido de aceleracion
q_a=9, R=25 (5 px de ruido de medida), P0=diag(100,100,400,400).
Parametros ajustables (tune en S1+S2, test en S3+S4): gate_min,
gate_max, gate_k, coast_max.

Uso:
    python scripts/exp1c-linker.py --pred docs/decisions/exp1b/pred1280-s1.json \\
        --seg s1 --out docs/decisions/exp1c/link-s1-g60-c3.json \\
        --gate-min 60 --gate-max 200 --gate-k 2.0 --coast-max 3 \\
        --reset-at ""
"""
import argparse
import json
import math
import time

import numpy as np


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pred", required=True, help="JSON pred1280 del tramo")
    p.add_argument("--seg", required=True, help="s1|s2|s3|s4")
    p.add_argument("--out", required=True, help="JSON de salida")
    p.add_argument("--gate-min", type=float, default=60.0,
                   help="radio minimo de la puerta (px/fotograma)")
    p.add_argument("--gate-max", type=float, default=200.0,
                   help="radio maximo de la puerta (px/fotograma)")
    p.add_argument("--gate-k", type=float, default=2.0,
                   help="radio crece gate_k * |v|")
    p.add_argument("--coast-max", type=int, default=3,
                   help="fotogramas que se predice sin deteccion (ESTIMADO)")
    p.add_argument("--reset-at", default="",
                   help="t_abs de cortes (coma) donde reiniciar")
    return p.parse_args()


class KalmanCV:
    """Filtro de Kalman de velocidad constante, estado [x, y, vx, vy]."""

    F = np.array([[1, 0, 1, 0], [0, 1, 0, 1],
                  [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)
    H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=float)
    Q = 9.0 * np.array([[0.25, 0, 0.5, 0], [0, 0.25, 0, 0.5],
                        [0.5, 0, 1, 0], [0, 0.5, 0, 1]], dtype=float)
    R = 25.0 * np.eye(2)

    def __init__(self, x, y, vx=0.0, vy=0.0):
        self.x = np.array([x, y, vx, vy], dtype=float)
        self.P = np.diag([100.0, 100.0, 400.0, 400.0])

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x[0], self.x[1]

    def update(self, zx, zy):
        z = np.array([zx, zy], dtype=float)
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(4) - K @ self.H) @ self.P
        return self.x[0], self.x[1]

    @property
    def pos(self):
        return float(self.x[0]), float(self.x[1])

    @property
    def vel(self):
        return float(self.x[2]), float(self.x[3])

    @property
    def speed(self):
        vx, vy = self.vel
        return math.hypot(vx, vy)


class Track:
    def __init__(self, tid, kf, bbox, conf):
        self.tid = tid
        self.kf = kf
        self.bbox = bbox      # ultima bbox observada [x0,y0,x1,y1]
        self.conf = conf
        self.coast = 0        # fotogramas consecutivos sin deteccion
        self.last_pos = kf.pos

    def center_bbox_at(self, cx, cy):
        x0, y0, x1, y1 = self.bbox
        w, h = x1 - x0, y1 - y0
        return [round(cx - w / 2, 1), round(cy - h / 2, 1),
                round(cx + w / 2, 1), round(cy + h / 2, 1)]


def main() -> int:
    args = parse_args()
    with open(args.pred, encoding="utf-8") as fh:
        data = json.load(fh)
    frames = data["frames"]
    resets = [float(x) for x in args.reset_at.split(",") if x.strip()]

    cfg = {
        "method": "linker-kalman-cv",
        "input": args.pred,
        "segment": args.seg,
        "classes_fed": ["sports ball"],
        "min_conf_fed": 0.05,
        "strong_init_conf": 0.25,
        "gate_min_px": args.gate_min,
        "gate_max_px": args.gate_max,
        "gate_k": args.gate_k,
        "coast_max_frames": args.coast_max,
        "velocity_coherence": "cos>0.3 si |v|>25 px/fotograma",
        "kalman": "CV fijo, q_a=9, R=25, P0=diag(100,100,400,400)",
        "resets_at_t_abs": resets,
        "note": "cortes manuales: ayuda experimental, no automatizada",
    }

    next_id = 1
    active = []    # Track
    pending = []   # (x, y, bbox, conf, t_abs) deteccion fuerte sin confirmar
    out_frames = []
    t0 = time.perf_counter()
    for fr in frames:
        t = fr["t_abs"]
        if any(abs(t - r) < 0.02 for r in resets):
            active, pending = [], []
        balls = [d for d in fr["detections"]
                 if d["cls"] == "sports ball" and d["conf"] >= 0.05]
        dets = []
        for d in balls:
            x0, y0, x1, y1 = d["bbox"]
            dets.append({"cx": (x0 + x1) / 2, "cy": (y0 + y1) / 2,
                         "bbox": d["bbox"], "conf": d["conf"]})
        used = [False] * len(dets)
        tracks_out = []

        # 1. Predecir tracks activos
        preds = {}
        for tr in active:
            preds[tr.tid] = tr.kf.predict()

        # 2. Asignacion voraz por distancia a la prediccion
        pairs = []
        for tr in active:
            px, py = preds[tr.tid]
            vx, vy = tr.kf.vel
            speed = tr.kf.speed
            radius = min(args.gate_max,
                         args.gate_min + args.gate_k * speed)
            for i, d in enumerate(dets):
                if used[i]:
                    continue
                dist = math.hypot(d["cx"] - px, d["cy"] - py)
                if dist > radius:
                    continue
                if speed > 25:
                    lx, ly = tr.last_pos
                    dx, dy = d["cx"] - lx, d["cy"] - ly
                    norm = math.hypot(dx, dy)
                    if norm > 1e-6:
                        cosang = (dx * vx + dy * vy) / (norm * speed)
                        if cosang < 0.3:
                            continue
                pairs.append((dist, tr.tid, i))
        pairs.sort()
        matched_tr, matched_det = set(), set()
        assign = {}  # tid -> indice de deteccion
        for _dist, tid, i in pairs:
            if tid in matched_tr or i in matched_det:
                continue
            matched_tr.add(tid)
            matched_det.add(i)
            assign[tid] = i
            used[i] = True

        # 3. Actualizar tracks emparejados; costear los demas
        new_active = []
        for tr in active:
            if tr.tid in matched_tr:
                d = dets[assign[tr.tid]]
                tr.kf.update(d["cx"], d["cy"])
                tr.bbox, tr.conf = d["bbox"], d["conf"]
                tr.coast = 0
                tr.last_pos = tr.kf.pos
                tracks_out.append({
                    "track_id": tr.tid, "bbox": d["bbox"],
                    "conf": round(float(d["conf"]), 3),
                    "det_conf": round(float(d["conf"]), 3),
                    "status": "observed"})
                new_active.append(tr)
            else:
                tr.coast += 1
                if tr.coast <= args.coast_max:
                    px, py = preds[tr.tid]
                    tracks_out.append({
                        "track_id": tr.tid,
                        "bbox": tr.center_bbox_at(px, py),
                        "conf": None, "det_conf": None,
                        "status": "estimated"})
                    new_active.append(tr)
                # si supera coast_max, el track termina (sin salida)
        active = new_active

        # 4. Confirmar pendientes con una segunda deteccion coherente
        new_pending = []
        for (px, py, pbbox, pconf, _pt) in pending:
            best, best_d = None, None
            for i, d in enumerate(dets):
                if used[i]:
                    continue
                dist = math.hypot(d["cx"] - px, d["cy"] - py)
                if dist <= args.gate_min and (best is None or dist < best):
                    best, best_d = dist, i
            if best_d is not None:
                d = dets[best_d]
                used[best_d] = True
                vx, vy = d["cx"] - px, d["cy"] - py
                kf = KalmanCV(d["cx"], d["cy"], vx, vy)
                tr = Track(next_id, kf, d["bbox"], d["conf"])
                next_id += 1
                tr.last_pos = kf.pos
                active.append(tr)
                tracks_out.append({
                    "track_id": tr.tid, "bbox": d["bbox"],
                    "conf": round(float(d["conf"]), 3),
                    "det_conf": round(float(d["conf"]), 3),
                    "status": "observed"})
            # si no se confirma, la pendiente se descarta (no se arrastra)
        pending = new_pending

        # 5. Nuevas pendientes: detecciones fuertes sin usar
        for i, d in enumerate(dets):
            if not used[i] and d["conf"] >= 0.25:
                pending.append((d["cx"], d["cy"], d["bbox"], d["conf"], t))

        out_frames.append({"frame": fr["frame"], "t_abs": t,
                           "tracks": tracks_out})
    wall = time.perf_counter() - t0

    n_tracks = len({tr["track_id"] for f in out_frames
                    for tr in f["tracks"]})
    result = {"config": cfg, "video": data.get("video"),
              "n_frames": len(out_frames), "n_tracks": n_tracks,
              "wall_s": round(wall, 3), "frames": out_frames}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh)
    print(f"{args.seg}: {len(out_frames)} fotogramas, {n_tracks} tracks, "
          f"{wall:.2f} s -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
