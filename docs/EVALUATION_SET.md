# Set de evaluación — clips y anotaciones humanas (Fase 0, 2026-11-06)

> Estado: **especificación y plantillas listas; clips pendientes**. Este documento define qué clips hacen falta y cómo se anotan. Los clips reales aún no están recogidos: hacen falta vídeos del usuario (o con su permiso) antes de ejecutar la Fase 1. No se evalúa sobre material usado para ajustar el sistema.

## 1. Composición mínima

| Grupo | Tipo de cámara | Clips | Duración c/u | Total |
|---|---|---|---|---|
| A | Táctica (plano amplio fijo o casi fijo) | 2 | 3–5 min | ~8 min |
| B | Retransmisión televisiva | 2 | 3–5 min | ~8 min |
| C | Amateur (móvil o cámara única, plano variable) | 2 | 2–3 min | ~5 min |
| **Total** | | **6** | | **~20 min** |

Requisitos por clip: un solo partido, sin cortes de edición entre jugadas (los cortes de realización televisiva sí forman parte del material y se anotan como segmentos), audio irrelevante, formato de los admitidos en v1 (MP4, MOV, MKV, AVI, WebM).

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

| ID | Grupo | Partido / fecha | Duración | Fuente | Uso | Estado |
|---|---|---|---|---|---|---|
| A1 | A | — | — | — | ajuste | pendiente |
| A2 | A | — | — | — | reservado | pendiente |
| B1 | B | — | — | — | ajuste | pendiente |
| B2 | B | — | — | — | reservado | pendiente |
| C1 | C | — | — | — | ajuste | pendiente |
| C2 | C | — | — | — | ajuste | pendiente |

Se rellena cuando el usuario aporte los vídeos. Solo se usan vídeos propios o con permiso para este uso.

## 6. Qué hace falta del usuario para cerrar este entregable

- Los 6 clips (o indicación de dónde están) con permiso de uso para evaluación interna.
- Confirmación de que pueden conservarse en el servidor Oracle, fuera del repo (los vídeos nunca van a Git).
- Si algún clip no puede compartirse, se sustituye por otro que cubra los mismos escenarios y se anota el cambio.
