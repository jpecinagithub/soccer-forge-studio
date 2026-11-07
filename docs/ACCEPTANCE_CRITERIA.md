# Criterios de aceptación — Fase 1 (Fase 0, 2026-11-06)

> **Dos bloques separados**, como exige la especificación: **A) prueba técnica automatizable** y **B) viabilidad**. Tener acceso no demuestra que el análisis sea suficientemente bueno: el bloque A puede pasar entero y el B suspender, y en ese caso la decisión es NO-GO.
>
> Todos los umbrales de este documento son **propuestos en Fase 0** y se fijan **antes** de ajustar ningún modelo. Si la primera medición queda sistemáticamente lejos de un umbral, la decisión es NO-GO o rediseño, no mover el umbral en silencio: cualquier cambio exige anotación con fecha y motivo.

## A. Bloque de prueba técnica automatizable (pasa / no pasa)

El Bloque A comprueba que el recorrido completo puede ejecutarse automáticamente desde la aplicación, sin intervención manual del agente Muse: subir un clip, procesarlo con las herramientas candidatas, generar eventos estructurados y abrir su evidencia. Se comprueba por cada solución candidata antes de medir viabilidad. Si un punto no pasa, no se empieza el bloque B con esa solución.

| ID | Comprobación | Cómo se verifica | Pasa si |
|---|---|---|---|
| A1 | Autenticación (si la solución usa API) | Una llamada real con la credencial de la cuenta; n/a si la solución es local | Responde 200 / sin error de auth, o no necesita credencial |
| A2 | Entrada de vídeo | Enviar un clip de 30 s en MP4 (y uno en MOV) | Ambos aceptados o rechazo con motivo claro |
| A3 | Límites documentados | Medir y anotar: duración máxima, resolución, tamaño, peticiones/min | Límites escritos en el informe, no supuestos |
| A4 | Comportamiento ante error | Enviar archivo corrupto y clip de 0 s | Error claro y sin cargo duplicado ni trabajo colgado |
| A5 | Salida estructurada | Pedir eventos con tiempos en JSON | La respuesta trae tiempos, tipos y confianza parseables |
| A6 | Coste observable | Registrar tokens / minutos facturados por llamada | El coste por llamada es visible y reproducible |
| A7 | Reintentos | Forzar un fallo transitorio (o documentar el observado) | El reintento no duplica el trabajo ni el cargo |
| A8 | Privacidad | Confirmar dónde se procesa y se conserva el vídeo | Queda escrito; si no se puede confirmar, NO-GO |

## B. Bloque de viabilidad (medible sobre el set de evaluación)

Se mide sobre los clips reservados (held-out) de `EVALUATION_SET.md`, con la referencia adjudicada como referencia. Un evento se considera acierto si coincide en tipo y participantes y `|ΔtStart| ≤ 1,0 s` (táctica) o `≤ 2,0 s` (TV / amateur).

### B1. Umbrales propuestos (Fase 0)

> **Cambios de criterio registrados antes del ensayo (2026-11-06, tras la revisión de B1):**
>
> 1. **Fórmula de F1 (corregida):** la versión anterior decía «aciertos / (omisiones + falsos positivos)», que no es F1. La fórmula correcta es **F1 = 2TP / (2TP + FP + FN)**, con emparejamiento uno a uno. Un evento detectado es TP solo si coincide en tipo y participantes y `|ΔtStart|` está dentro de la tolerancia; en caso contrario es FP, y cada evento anotado sin pareja es FN.
> 2. **Tiempo analizable (redefinido para resúmenes editados):** el umbral ≥ 70 % (TV) no se aplica sobre la duración total del clip, porque en un resumen editado gran parte del tiempo son primeros planos y repeticiones. Se separan dos medidas: **cobertura de observación del clip** = tiempo `field-view` / duración total (B1 v2: 131,00 s / 237,24 s ≈ 55,2 %, se informa y no se exige); **tiempo analizable** = tiempo `field-view` procesado con éxito / tiempo `field-view` total, y el umbral ≥ 70 % se aplica a esta segunda medida. La vista de campo no acredita por sí sola la calibración geométrica: la calibración se verifica aparte, solo en tramos con geometría válida.
> 3. **Ámbito de puntuación:** los umbrales de F1 se miden solo sobre los eventos y ventanas que la anotación marca como puntuables en su campo `scoring` (`scoredEvents`); los casos pendientes (`pendingNotScored`) no cuentan como TP, FP ni FN hasta su adjudicación. No se calcula F1 global de una clase (pases, pérdidas, recuperaciones) sobre un clip cuya anotación de esa clase es parcial.
> 4. **Referencia (2026-11-07):** la anotación v2 de B1 es material exploratorio hecha por Muse, sin adjudicación humana. Sirve para desarrollar y para probar el procedimiento de medición, pero **no es una prueba formal de ningún motor** y **no puede usarse a la vez como predicción del sistema y como referencia para puntuarlo**. La comparación final se puntúa contra la referencia adjudicada del clip reservado.
> 5. **Tiempo de proceso (2026-11-07):** el umbral ≤ 3× real pasa a ser **objetivo de rendimiento en esta etapa, no criterio de corte**. La calidad y la trazabilidad son requisitos obligatorios. No se descarta una solución solo por superar 3× en esta etapa; cualquier cambio de este criterio se documenta antes de medir.

| Métrica | Cámara táctica | TV / amateur | Cómo se mide |
|---|---|---|---|
| F1 de pases | ≥ 0,70 | ≥ 0,55 | F1 = 2TP / (2TP + FP + FN), con emparejamiento uno a uno entre eventos detectados y anotados (mismo tipo y participantes, \|ΔtStart\| dentro de la tolerancia); si la referencia marca `unknownPlayers`, la identidad no se penaliza (solo tipo y tiempo) |
| F1 de tiros | ≥ 0,70 | ≥ 0,55 | idem |
| F1 de recuperaciones + pérdidas | ≥ 0,60 | ≥ 0,45 | idem |
| Error mediano en inicio/fin de jugada | ≤ 1,0 s | ≤ 2,0 s | mediana de \|Δt\| |
| Cambios indebidos de identidad | ≤ 2 por 10 min | ≤ 4 por 10 min | conteo manual sobre trayectorias |
| Error mediano de posición (donde hay referencia válida) | ≤ 1,5 m | ≤ 3,0 m | solo tramos `field-view` calibrados |
| Tiempo analizable | ≥ 85 % | ≥ 70 % | ver nota de cambio 2026-11-06 bajo la tabla: se mide sobre el material elegible, no sobre la duración total del clip |
| Jugadas con evidencia que abre | 100 % | 100 % | clic en cada jugada del informe |
| Correcciones que persisten tras recargar | 100 % | 100 % | corrección → recarga → comprobación |
| Incertidumbre calibrada | ≥ 60 % de los errores estaban marcados `pending` o con confianza < 0,60 | idem | errores revisados a mano |
| Esfuerzo de corrección | ≤ 20 min de analista por 10 min de vídeo | ≤ 30 min | tiempo medido |
| Tiempo de proceso (CPU, sin GPU) | objetivo ≤ 3× tiempo real (p50) | objetivo ≤ 3× tiempo real (p50) | 10 min procesados en ≤ 30 min; en esta fase es objetivo, no criterio de corte (cambio 2026-11-07) |
| Coste por minuto | Se mide y se informa; no es criterio de corte | idem | €/min medidos. Decisión del usuario 2026-11-06: el presupuesto no es una restricción (proyecto educativo) |

### B2. Comparación de soluciones de análisis integrables

- **Mismo material:** los clips reservados; **misma referencia:** la anotación adjudicada; **misma puntuación:** la tabla B1. Cada solución candidata produce sus predicciones; la referencia nunca es la salida de una de las soluciones comparadas.
- **Regla de decisión:** gana la solución que cumple todos los umbrales de B1; si varias los cumplen, se elige la más simple y barata de operar. Si ninguna los cumple, la decisión es NO-GO o rediseño, no se construye el sistema complejo por inercia.
- **Coste:** la comparación incluye tiempo y coste por minuto de cada opción, solo como información. El coste no bloquea la decisión (proyecto educativo, decisión del usuario 2026-11-06).

## C. Decisión

| Resultado | Decisión |
|---|---|
| A pasa entero y B cumple todos los umbrales | **GO** a Fase 2 (ingesta) con el diseño medido |
| A pasa, B falla en 1–2 métricas no críticas (no evidencia, no correcciones, no tiempo) | **CONDICIONAL**: se documenta el fallo, se fija un plan de corrección y se repite la medición; sin repetición no hay GO |
| A falla, o B falla en evidencia, correcciones o tiempo | **NO-GO**: no se construye el dashboard completo; se rediseña o se cambia de solución |
| B no se puede medir (sin clips, sin anotaciones) | **SIN MEDICIÓN**: no hay decisión; el paso previo es cerrar `EVALUATION_SET.md` |

## D. Registro de la decisión

Cada ejecución de la Fase 1 deja un informe en `docs/decisions/` con: fecha, clips usados, configuración, tabla B1 medida, costes, decisión (GO / CONDICIONAL / NO-GO) y, si cambia un umbral, fecha y motivo del cambio.
