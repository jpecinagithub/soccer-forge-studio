#!/usr/bin/env python3
"""Puntúa las predicciones del experimento 2 (Qwen) SOLO en tiros y
desenlaces, contra los 5 eventos puntuables de la anotación v2 de B1.

Uso:
    python3 scripts/score-exp2.py <pred1.json> [<pred2.json> ...] \\
        --offsets 35 60 90 120 ...

Cada predicción lleva su desplazamiento (offset) en segundos del vídeo
original, en el mismo orden. Los tiempos de la predicción son relativos
a su ventana; se convierten a absolutos sumando el offset.

Reglas (ACCEPTANCE_CRITERIA.md, TV, tolerancia 2.0 s):
- Solo se puntúan eventos de tipo "shot" de la predicción.
- Un tiro puntuable es TP si hay un tiro predicho con |ΔtStart| ≤ 2.0 s
  y el mismo resultado (goal/saved). Si el resultado difiere, se cuenta
  como "resultado incorrecto", no como TP.
- Un tiro predicho que no empareja con ningún evento de la referencia
  (puntuable o pendiente) en 2.0 s se lista como "sin pareja" (posible
  falso positivo; no se convierte en F1: la anotación es parcial).
- Un tiro predicho que empareja con un evento pendiente (no puntuable)
  se lista como "empareja con pendiente": no es TP ni FP.
- NO se evalúan F1 de pases, seguimiento ni posiciones.

La referencia nunca se entrega al motor: este script solo se ejecuta
offline, después de la predicción.
"""

import argparse
import json

TOL = 2.0
REF_PATH = "docs/evaluation/B1-georgia-espana-annotation.json"


def load_predictions(paths, offsets):
    events = []
    for path, offset in zip(paths, offsets):
        pred = json.load(open(path))
        for play in pred.get("plays", []):
            for ev in play.get("events", []):
                if ev.get("type") != "shot":
                    continue
                events.append({
                    "tStart": ev["tStart"] + offset,
                    "tEnd": ev["tEnd"] + offset,
                    "result": ev.get("result"),
                    "players": ev.get("players", []),
                    "uncertainty": ev.get("uncertainty", {}),
                    "src": f"{path} (offset {offset})",
                })
    return events


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("preds", nargs="+")
    ap.add_argument("--offsets", type=float, nargs="+", required=True)
    args = ap.parse_args()
    if len(args.preds) != len(args.offsets):
        print("ERROR: nº de predicciones distinto del nº de offsets")
        return 2

    ref = json.load(open(REF_PATH))
    scored_ids = set(ref["scoring"]["scoredEvents"])
    all_ref = []
    for play in ref["plays"]:
        for ev in play["events"]:
            all_ref.append({
                "id": ev["id"], "play": play["id"], "type": ev["type"],
                "tStart": ev["tStart"], "tEnd": ev["tEnd"],
                "result": ev.get("result"),
                "scored": ev["id"] in scored_ids,
            })
    scored_shots = [e for e in all_ref
                    if e["scored"] and e["type"] == "shot"]
    pred_shots = load_predictions(args.preds, args.offsets)

    print(f"Tiros predichos: {len(pred_shots)} | "
          f"Tiros puntuables en la referencia: {len(scored_shots)}")
    print()
    tp = 0
    wrong_result = []
    missed = []
    used = set()
    for s in scored_shots:
        cands = [(i, p) for i, p in enumerate(pred_shots)
                 if i not in used
                 and abs(p["tStart"] - s["tStart"]) <= TOL]
        if not cands:
            missed.append(s)
            continue
        i, p = min(cands, key=lambda c: abs(c[1]["tStart"] - s["tStart"]))
        used.add(i)
        if p["result"] == s["result"]:
            tp += 1
            print(f"  TP  {s['id']} ({s['play']}): ref {s['tStart']:.2f} "
                  f"-> {s['result']} | pred {p['tStart']:.2f} "
                  f"-> {p['result']} (Δ={p['tStart'] - s['tStart']:+.2f} s)")
        else:
            wrong_result.append((s, p))
            print(f"  RES {s['id']} ({s['play']}): ref {s['tStart']:.2f} "
                  f"-> {s['result']} | pred {p['tStart']:.2f} "
                  f"-> {p['result']} (Δ={p['tStart'] - s['tStart']:+.2f} s)")
    for s in missed:
        print(f"  FN  {s['id']} ({s['play']}): ref {s['tStart']:.2f} "
              f"-> {s['result']} | sin tiro predicho en ±{TOL} s")
    print()
    print("Tiros predichos sin pareja con ningún evento de la referencia:")
    for i, p in enumerate(pred_shots):
        if i in used:
            continue
        near = [e for e in all_ref
                if abs(p["tStart"] - e["tStart"]) <= TOL]
        if near:
            e = near[0]
            tag = "pendiente" if not e["scored"] else "puntuable"
            print(f"  ~   pred {p['tStart']:.2f} -> {p['result']} | "
                  f"empareja con {e['id']} ({tag}, ref {e['tStart']:.2f})")
        else:
            print(f"  FP? pred {p['tStart']:.2f} -> {p['result']} | "
                  f"sin evento de referencia en ±{TOL} s")
    print()
    print(f"Resumen tiros puntuables: TP {tp}/{len(scored_shots)}, "
          f"resultado incorrecto {len(wrong_result)}, "
          f"no detectados {len(missed)}")
    print("No se calcula F1 (la anotación de tiros es parcial y la "
          "muestra es de 5 eventos).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
