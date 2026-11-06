# Set de evaluación — clips y anotaciones humanas (Fase 0, 2026-11-06)

> Estado 2026-11-06: **piloto con 1 clip recibido y verificado** (B1, Georgia 0-4 España, 237,24 s, SHA256 comprobado). **Anotación humana: primer pase hecho 2026-11-06 y corregido a v2 el mismo día** (`docs/evaluation/B1-georgia-espana-annotation.json`, 8 jugadas, 11 eventos, 5 puntuables, 4 goles), tras revisión por IA del 33 % de las jugadas + 2 tramos (`docs/evaluation/REVISION-B1.md`). **Adjudicación humana pendiente**: esta referencia NO es una anotación humana validada. El resto del set sigue pendiente. No se evalúa sobre material usado para ajustar el sistema.

## 1. Composición mínima

| Grupo | Tipo de cámara | Clips | Duración c/u | Total |
|---|---|---|---|---|
| A | Táctica (plano amplio fijo o casi fijo) | 2 | 3–5 min | ~8 min |
| B | Retransmisión televisiva | 2 | 3–5 min | ~8 min |
| C | Amateur (móvil o cámara única, plano variable) | 2 | 2–3 min | ~5 min |
| **Total** | | **6** | | **~20 min** |

Requisitos por clip: un solo partido, sin cortes de edición entre jugadas (los cortes de realización televisiva sí forman parte del material y se anotan como segmentos), audio irrelevante, formato de los admitidos en v1 (MP4, MOV, MKV, AVI, WebM).

**Piloto:** la Fase 1 empieza con un solo clip (B1) para validar el procedimiento de medición antes de ampliar el set. Los umbrales de `ACCEPTANCE_CRITERIA.md` se aplican igual; la cobertura de escenarios del piloto es parcial y se anota como tal.

## 2. Matriz de cobertura (cada escenario, al menos en un clip)

- [ ] Oclusión de jugadores (≥ 3 casos)
- [ ] Movimiento de cámara: paneo y zoom (grupo B y C)
- [ ] Primer plano (`close-up`) de ≥ 5 s
- [ ] Repetición televisiva de una jugada (grupo B)
- [ ] Balón poco visible o fuera de cuadro ≥ 2 s
- [ ] Cambio de iluminación o sombra pronunciada
- [ ] Jugada a balón parado: falta, córner o saque de banda
- [ ] Contraataque con cambio rápido de posesión
- [ ] Disparo a portería (al menos 1 por grupo, si el material lo permite)
- [ ] Pérdida en salida de balón

Si un escenario no aparece en los clips disponibles, se anota como **no cubierto**; no se simula ni se inventa.

**Cobertura del piloto (B1):** el clip es un resumen televisivo editado: incluye primeros planos (p. ej. revisión VAR) y posibles repeticiones, pero no es juego continuo. Los escenarios que no aparezcan quedan como no cubiertos en el informe del piloto.

## 3. División: ajuste vs evaluación

- **Ajuste (dev):** 4 clips (A1, B1, C1 y uno a elegir). Sobre estos se puede iterar, depurar y fijar parámetros.
- **Reservado (held-out):** 2 clips (uno táctico o TV y uno amateur), de **partidos distintos** a los de ajuste. No se usan para ajustar nada. Solo se evalúan una vez por configuración, con el procedimiento de `ACCEPTANCE_CRITERIA.md`.
- **Regla:** un resultado medido solo sobre el material de ajuste no es un resultado de viabilidad.

## 4. Protocolo de anotación humana

1. **Anotador:** una persona con conocimiento de fútbol anota cada clip completo viendo el vídeo a velocidad normal, con pausa y avance preciso para los límites.
2. **Qué se anota por jugada:** `tStart`, `tEnd`, equipo, lista de eventos (tipo, `tStart`, `tEnd`, pasador/receptor o participantes, resultado) y, si se conoce, periodo y reloj del partido.
3. **Casos dudosos:** se anotan con `uncertain: true` y nota; no se fuerza una decisión.
4. **Repeticiones:** se anotan como segmentos `replay` vinculados a la jugada original en directo; no generan jugadas nuevas.
5. **Revisión:** al menos el 20 % de las jugadas (o un clip completo) lo revisa una segunda persona; los desacuerdos quedan registrados y se resuelven antes de evaluar.
6. **Formato:** un fichero JSON por clip, siguiendo `docs/evaluation/annotation-template.json`. Los tiempos son segundos del archivo con dos decimales.

## 5. Inventario de clips

Los tres resúmenes RFEF están identificados (fuente: `data/clips/FUENTES.md`, descargados de rfef.es el 2026-11-06; H.264 1920×1080, AAC). Solo B1 está recibido y verificado. Los vídeos nunca van a Git (`data/` está ignorado); la procedencia se conserva en `data/clips/`.

| ID | Grupo | Partido / fecha | Duración | Fuente | Uso | Estado |
|---|---|---|---|---|---|---|
| A1 | A | — | — | — | ajuste | pendiente |
| A2 | A | — | — | — | reservado | pendiente |
| B1 | B | Georgia 0-4 España | 237,24 s | RFEF | ajuste (piloto) | **recibido y verificado 2026-11-06** (SHA256 `6e7d037e…`, MP4 587.042.519 bytes); **anotación v2** (`docs/evaluation/B1-georgia-espana-annotation.json`, 8 jugadas, 11 eventos, 5 puntuables), adjudicación humana pendiente |
| B2 | B | España 2-0 Georgia | 130,64 s | RFEF | reservado | identificado, pendiente de recibir |
| B3 | B | España 4-0 Bulgaria | 146,72 s | RFEF | ajuste | identificado, pendiente de recibir |
| C1 | C | — | — | — | ajuste | pendiente |
| C2 | C | — | — | — | ajuste | pendiente |

Nota: `espana-georgia-2025.info.json` corresponde a un intento fallido de RTVE, no a un clip descargado.

## 6. Qué hace falta para cerrar este entregable

- Recibido B1 (piloto) y anotado en v2 el 2026-11-06 (8 jugadas, 11 eventos, 5 puntuables; revisión por IA del 33 % + 2 tramos en `docs/evaluation/REVISION-B1.md`; adjudicación humana pendiente). Pendientes: completar la anotación exhaustiva de las ventanas puntuadas antes del ensayo del bloque B; B2, B3 (identificados, en RFEF) y los grupos A (táctica) y C (amateur), aún sin fuente.
- Los vídeos se conservan fuera del repo, en el servidor Oracle cuando se despliegue (o en `data/clips/` local hasta entonces).
- Solo se usan vídeos propios o con permiso para este uso. La disponibilidad pública de los resúmenes RFEF no acredita una licencia de redistribución: no se publican en GitHub ni se envían a Meta.
