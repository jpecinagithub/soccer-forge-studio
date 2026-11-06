# Criterios de aceptación — Fase 1 (Fase 0, 2026-11-06)

> **Dos bloques separados**, como exige la especificación: **A) acceso técnico** y **B) viabilidad**. Tener acceso no demuestra que el análisis sea suficientemente bueno: el bloque A puede pasar entero y el B suspender, y en ese caso la decisión es NO-GO.
>
> Todos los umbrales de este documento son **propuestos en Fase 0** y se fijan **antes** de ajustar ningún modelo. Si la primera medición queda sistemáticamente lejos de un umbral, la decisión es NO-GO o rediseño, no mover el umbral en silencio: cualquier cambio exige anotación con fecha y motivo.

## A. Bloque de acceso técnico (pasa / no pasa)

Se comprueba antes de medir viabilidad. Si un punto no pasa, no se empieza el bloque B con ese proveedor o configuración.

| ID | Comprobación | Cómo se verifica | Pasa si |
|---|---|---|---|
| A1 | Autenticación | Una llamada real con la credencial de la cuenta | Responde 200 / sin error de auth |
| A2 | Entrada de vídeo | Enviar un clip de 30 s en MP4 (y uno en MOV) | Ambos aceptados o rechazo con motivo claro |
| A3 | Límites documentados | Medir y anotar: duración máxima, resolución, tamaño, peticiones/min | Límites escritos en el informe, no supuestos |
| A4 | Comportamiento ante error | Enviar archivo corrupto y clip de 0 s | Error claro y sin cargo duplicado ni trabajo colgado |
| A5 | Salida estructurada | Pedir eventos con tiempos en JSON | La respuesta trae tiempos, tipos y confianza parseables |
| A6 | Coste observable | Registrar tokens / minutos facturados por llamada | El coste por llamada es visible y reproducible |
| A7 | Reintentos | Forzar un fallo transitorio (o documentar el observado) | El reintento no duplica el trabajo ni el cargo |
| A8 | Privacidad | Confirmar dónde se procesa y se conserva el vídeo | Queda escrito; si no se puede confirmar, NO-GO |

## B. Bloque de viabilidad (medible sobre el set de evaluación)

Se mide sobre los clips reservados (held-out) de `EVALUATION_SET.md`, con las anotaciones humanas como referencia. Un evento se considera acierto si coincide en tipo y participantes y `|ΔtStart| ≤ 1,0 s` (táctica) o `≤ 2,0 s` (TV / amateur).

### B1. Umbrales propuestos (Fase 0)

| Métrica | Cámara táctica | TV / amateur | Cómo se mide |
|---|---|---|---|
| F1 de pases | ≥ 0,70 | ≥ 0,55 | aciertos / (omisiones + falsos positivos) por tipo |
| F1 de tiros | ≥ 0,70 | ≥ 0,55 | idem |
| F1 de recuperaciones + pérdidas | ≥ 0,60 | ≥ 0,45 | idem |
| Error mediano en inicio/fin de jugada | ≤ 1,0 s | ≤ 2,0 s | mediana de \|Δt\| |
| Cambios indebidos de identidad | ≤ 2 por 10 min | ≤ 4 por 10 min | conteo manual sobre trayectorias |
| Error mediano de posición (donde hay referencia válida) | ≤ 1,5 m | ≤ 3,0 m | solo tramos `field-view` calibrados |
| Tiempo analizable | ≥ 85 % | ≥ 70 % | `analyzableSec / totalSec` |
| Jugadas con evidencia que abre | 100 % | 100 % | clic en cada jugada del informe |
| Correcciones que persisten tras recargar | 100 % | 100 % | corrección → recarga → comprobación |
| Incertidumbre calibrada | ≥ 60 % de los errores estaban marcados `pending` o con confianza < 0,60 | idem | errores revisados a mano |
| Esfuerzo de corrección | ≤ 20 min de analista por 10 min de vídeo | ≤ 30 min | tiempo medido |
| Tiempo de proceso (CPU, sin GPU) | ≤ 3× tiempo real (p50) | ≤ 3× tiempo real (p50) | 10 min procesados en ≤ 30 min |
| Coste por minuto | ≤ presupuesto fijado por el usuario antes de la Fase 1 | idem | €/min medidos; **sin presupuesto fijado no hay GO** |

### B2. Comparación Muse directo vs Muse con herramientas de visión

- **Mismo material:** los clips reservados; **misma anotación:** la referencia humana; **misma puntuación:** la tabla B1.
- **Regla de decisión:** el sistema combinado (Muse + herramientas) debe superar a Muse directo en **F1 de pases ≥ +0,05 o error mediano de jugada ≥ −20 %**. Si no lo supera, se elige la opción más simple o se rediseña; no se construye el sistema complejo por inercia.
- **Coste:** la comparación incluye tiempo y coste por minuto de cada opción. Una mejora pequeña con un coste mucho mayor es NO-GO para esa opción.

## C. Decisión

| Resultado | Decisión |
|---|---|
| A pasa entero y B cumple todos los umbrales | **GO** a Fase 2 (ingesta) con el diseño medido |
| A pasa, B falla en 1–2 métricas no críticas (no evidencia, no correcciones, no tiempo) | **CONDICIONAL**: se documenta el fallo, se fija un plan de corrección y se repite la medición; sin repetición no hay GO |
| A falla, o B falla en evidencia, correcciones, tiempo o coste | **NO-GO**: no se construye el dashboard completo; se rediseña o se cambia de proveedor |
| B no se puede medir (sin clips, sin anotaciones) | **SIN MEDICIÓN**: no hay decisión; el paso previo es cerrar `EVALUATION_SET.md` |

## D. Registro de la decisión

Cada ejecución de la Fase 1 deja un informe en `docs/decisions/` con: fecha, clips usados, configuración, tabla B1 medida, costes, decisión (GO / CONDICIONAL / NO-GO) y, si cambia un umbral, fecha y motivo del cambio.
