#!/usr/bin/env python3
"""Valida la respuesta de un modelo al fragmento B1 35-65 s.

Uso: validate-fragment-response.py <respuesta.json> [--offset 35.0]

Comprueba:
  1. El JSON es válido y cumple fragment-response-schema.json.
  2. Los segmentos cubren [0, 30] sin huecos ni solapamientos.
  3. Todos los tiempos están dentro del fragmento.
  4. Las repeticiones no generan jugadas nuevas (toda jugada cae en
     vista de campo, no dentro de un segmento replay).
  5. Coherencia con la referencia v2 (desplazada por --offset):
     - penalti: golpeo en 45.50 (rel. 10.50), gol en 46.25 (rel. 11.25)
     - tiro play-C: 55.80-56.80 (rel. 20.80-21.80), resultado no resuelto
     - repetición de play-A en 35.00-36.00 (rel. 0.00-1.00)
  6. Los eventos con players vacíos marcan uncertainty.identity.
  7. Los eventos con result null marcan uncertainty.result.

La comparación con la referencia es informativa (tolerancia 2.0 s en TV),
no un aprobado/suspenso: el ensayo exploratorio no calcula F1.
"""

import json
import sys

import jsonschema

OFFSET = 35.0
FRAG_LEN = 30.0
TOL = 2.0
SCHEMA_PATH = "docs/evaluation/fragment-response-schema.json"

# Referencia v2, tiempos absolutos -> relativos al fragmento
REF = {
    "penalty_kick": 45.50 - OFFSET,   # 10.50
    "penalty_goal": 46.25 - OFFSET,   # 11.25
    "shot_c_start": 55.80 - OFFSET,   # 20.80
    "shot_c_end": 56.80 - OFFSET,     # 21.80
    "replay_a": (35.00 - OFFSET, 36.00 - OFFSET),  # (0.00, 1.00)
}


def check(cond, label, problems):
    print(("  OK  " if cond else "  FALLO  ") + label)
    if not cond:
        problems.append(label)
    return cond


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    problems: list[str] = []

    try:
        resp = json.load(open(path))
    except Exception as exc:
        print("FALLO: el JSON no es válido:", exc)
        return 1

    schema = json.load(open(SCHEMA_PATH))
    try:
        jsonschema.validate(resp, schema)
        print("  OK   esquema fragment-response-schema.json")
    except jsonschema.ValidationError as exc:
        print("  FALLO  esquema:", exc.message)
        problems.append("esquema")

    segs = resp.get("segments", [])
    covered = sorted(segs, key=lambda s: s["tStart"])
    continuous = (
        covered
        and abs(covered[0]["tStart"] - 0.0) < 0.01
        and abs(covered[-1]["tEnd"] - FRAG_LEN) < 0.01
        and all(abs(a["tEnd"] - b["tStart"]) < 0.01 for a, b in zip(covered, covered[1:]))
    )
    check(continuous, "segmentos cubren [0, 30] sin huecos ni solapamientos", problems)

    plays = resp.get("plays", [])
    in_range = all(
        0 <= p["tStart"] < p["tEnd"] <= FRAG_LEN
        and all(0 <= e["tStart"] < e["tEnd"] <= FRAG_LEN for e in p["events"])
        for p in plays
    )
    check(in_range, "todos los tiempos dentro del fragmento", problems)

    replay_ranges = [(s["tStart"], s["tEnd"]) for s in segs if s["type"] == "replay"]
    play_in_replay = any(
        any(rs <= p["tStart"] < re for rs, re in replay_ranges) for p in plays
    )
    check(not play_in_replay, "ninguna jugada empieza dentro de una repetición", problems)

    # Referencia informativa (tolerancia TV 2.0 s)
    events = [e for p in plays for e in p["events"]]
    shots = [e for e in events if e["type"] == "shot"]
    kick = any(abs(e["tStart"] - REF["penalty_kick"]) <= TOL for e in shots)
    check(kick, f"penalti detectado cerca de {REF['penalty_kick']:.2f} s rel.", problems)
    goal = any(
        e.get("result") == "goal" and abs(e["tStart"] - REF["penalty_kick"]) <= TOL
        for e in shots
    )
    check(goal, "penalti marcado como gol", problems)
    shot_c = any(abs(e["tStart"] - REF["shot_c_start"]) <= TOL for e in shots)
    check(shot_c, f"tiro play-C detectado cerca de {REF['shot_c_start']:.2f} s rel.", problems)
    c_unresolved = any(
        abs(e["tStart"] - REF["shot_c_start"]) <= TOL and e.get("result") is None
        for e in shots
    )
    check(c_unresolved, "tiro play-C con resultado no resuelto (null)", problems)
    replay_flagged = any(
        abs(s["tStart"] - REF["replay_a"][0]) <= TOL and s["type"] == "replay"
        for s in segs
    )
    check(replay_flagged, "repetición inicial (0-1 s) clasificada como replay", problems)

    unknown_ok = all(
        (len(e.get("players", [])) > 0) or e["uncertainty"]["identity"] for e in events
    )
    check(unknown_ok, "jugadores desconocidos marcados como inciertos", problems)
    result_ok = all(
        (e.get("result") is not None) or e["uncertainty"]["result"] for e in events
    )
    check(result_ok, "resultados no resueltos marcados como inciertos", problems)

    print()
    print(f"Jugadas: {len(plays)} | Eventos: {len(events)} | Segmentos: {len(segs)}")
    if problems:
        print(f"RESULTADO: {len(problems)} comprobaciones fallidas (ver arriba)")
        return 1
    print("RESULTADO: todas las comprobaciones pasaron")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
