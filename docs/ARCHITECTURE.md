# Arquitectura — Soccer Forge Studio

> Fase 0. Las decisiones aquí son el plan; los contratos exactos (esquemas, endpoints) se cierran en la Fase 0 y se prueban en la Fase 1.

## Monorepo

```
apps/web          Vite + React + TS — dashboard
apps/api          Node 20 + TS — REST, subida, biblioteca, correcciones, exportación
apps/worker       Node 20 + TS — pipeline de análisis
packages/shared   Tipos y contratos (eventos, jugadas, estados de trabajo)
infra/deploy      docker-compose.yml + nginx
docs/             SPEC, DEPLOYMENT, ARCHITECTURE, EVENT_DICTIONARY
```

Gestor de paquetes y lockfile por definir en la Fase 2 (el host usa Node v20.20.2; fijar la versión del gestor para que el build del servidor no falle por una versión distinta).

## Pipeline (10 etapas, cada una guarda su resultado)

| Etapa | Trabajo | Resultado verificable |
|---|---|---|
| Recepción | Validar archivo, duración, resolución, decodificación | Vídeo aceptado o motivo de rechazo |
| Preparación | Copia de trabajo conservando tiempos | Reproducción y análisis alineados con el original |
| Segmentación | Planos, cortes, repeticiones, interrupciones | Tramos analizables y excluidos |
| Percepción | Detectar jugadores, árbitros y balón | Observaciones con tiempo y confianza |
| Seguimiento | Asociar observaciones, resolver identidades | Trayectorias y asociaciones revisables |
| Calibración | Relacionar imagen y campo, compensar cámara | Posiciones y calidad de calibración |
| Eventos | Detectar acciones y agruparlas en jugadas | Catálogo estructurado |
| Revisión con Muse | Casos ambiguos y contexto táctico | Explicaciones vinculadas a evidencias |
| Validación | Coherencia, duplicados, cobertura | Informe de calidad |
| Publicación | Datos, clips e índices | Dashboard consultable |

El procesamiento se divide en segmentos con contexto solapado; después se reconcilian identidades y eventos entre segmentos para evitar duplicados o jugadas cortadas. Un fallo recuperable no obliga a repetir todo el partido ni a duplicar cargos o registros. El agente puede reexaminar una secuencia con más detalle, con límites de intentos, tiempo y coste; si no resuelve una duda, la publica como pendiente.

## Datos

- **Postgres:** partidos, jugadores, eventos, jugadas, análisis, correcciones (con historial).
- **Redis:** cola persistente de trabajos (etapas, reintentos, progreso).
- **Volumen de medios:** originales, copias de trabajo, clips.
- **Registro por análisis:** versión del pipeline, duración, consumo y errores.

Corregir un jugador o un evento actualiza las estadísticas dependientes. Todas las correcciones se conservan.

## Contratos (resumen; esquemas exactos en Fase 0)

- **Evento:** `{ id, matchId, type, tStart, tEnd, teamId?, playerIds[], result, location?, confidence, evidenceClipId, status }`.
- **Jugada:** `{ id, matchId, tStart, tEnd, events[], participants, interpretation?, quality, evidenceClipId, reviewStatus }`.
- **Trabajo de análisis:** `{ id, matchId, stage, stageStatus, progress, error?, qualityReport? }`.
- Tiempo del archivo y reloj del partido, siempre separados. Una repetición televisiva no se contabiliza como otra acción.

## Dashboard

Cinco áreas: Vídeo · Campo 2D · Jugadas · Línea temporal · Inspector. Más resumen del partido, jugadores, métricas y exportaciones. El chat llega después de tener datos fiables y debe devolver jugadas concretas con enlaces al vídeo, o indicar falta de evidencia.

## Muse (agente de Meta)

Dos usos separados: Muse como herramienta de desarrollo, y Muse dentro del producto (coordinar herramientas, revisar secuencias, generar explicaciones tácticas). Las herramientas especializadas aportan detecciones, trayectorias y mediciones. Antes de integrar: comprobar qué puede hacer el agente con el vídeo, límites de entrada y herramientas disponibles (Fase 1).

> Corrección 2026-11-07: el agente del proyecto es Muse de Meta, que funciona con Muse Spark 1.3. No es el modelo `muse-spark-1.3` alojado en OpenCode: ese es otro producto con un nombre parecido. El informe `docs/decisions/block-a-2026-11-07.md` documenta el estado de esa vía de OpenCode (sin acceso gratuito utilizable), pero no es la vía del proyecto.
