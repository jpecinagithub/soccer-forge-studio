# Contrato de datos — jugada y evidencia (Fase 0, v0.1.0, 2026-11-06)

> **Fuente normativa** para la implementación (Fases 2–5). Los esquemas exactos de validación (JSON Schema / zod) se derivan de este documento en la Fase 2; si hay conflicto, manda este documento hasta que se apruebe una nueva versión con fecha.
>
> Todas las referencias temporales son **segundos del archivo** (dos decimales), salvo los campos marcados explícitamente como reloj de partido. Los IDs son UUID. `null` significa "desconocido", nunca "no aplica".

## 1. Entidades

### 1.1 `Match` — partido

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `id` | UUID | sí | |
| `title` | string | sí | |
| `homeTeamId` / `awayTeamId` | UUID \| null | no | opcionales en v1 |
| `videoFile` | objeto | sí | `originalName`, `format`, `durationSec`, `width`, `height`, `sha256` |
| `status` | enum | sí | `uploaded` · `processing` · `done` · `partial` · `failed` |
| `createdAt` | timestamp | sí | |
| `limitations` | string[] | sí | puede ser lista vacía; nunca se omite |

### 1.2 `Segment` — tramo del archivo

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `id` | UUID | sí | |
| `matchId` | UUID | sí | |
| `tStart` / `tEnd` | number | sí | `tEnd > tStart`; los segmentos cubren el archivo sin solaparse |
| `type` | enum | sí | `field-view` · `close-up` · `replay` · `excluded` |
| `calibrationQuality` | number \| null | sí* | 0..1 si `type = field-view`; `null` en el resto |
| `replayOfEventId` | UUID \| null | no | solo en `replay`: el evento original en directo al que corresponde |

### 1.3 `EvidenceClip` — evidencia

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `id` | UUID | sí | |
| `matchId` | UUID | sí | |
| `tStart` / `tEnd` | number | sí | debe cubrir íntegramente el evento o jugada que referencia, con 0,5 s de margen a cada lado cuando el material lo permita |
| `sourceSegmentId` | UUID | sí | el segmento en directo del que procede; en una repetición, el segmento en directo, no la repetición |
| `storagePath` | string | sí | ruta en el volumen de medios, p. ej. `matches/<matchId>/clips/<id>.mp4` |
| `thumbnailPath` | string \| null | no | |

**Regla de oro:** ninguna jugada y ningún evento existen sin `evidenceClipId` válido. Un enlace roto invalida la publicación de esa jugada.

### 1.4 `MatchEvent` — evento

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `id` | UUID | sí | |
| `matchId` / `playId` | UUID | sí | |
| `type` | enum | sí | `pass` · `carry` · `recovery` · `loss` · `shot` (ver `EVENT_DICTIONARY.md`) |
| `tStart` / `tEnd` | number | sí | `tEnd >= tStart` |
| `teamId` | UUID \| null | sí* | `null` solo con `unknown: true` |
| `playerIds` | UUID[] | sí | puede ser vacía; cada ID desconocido se representa con `unknownPlayers: true` |
| `unknownPlayers` | boolean | sí | |
| `result` | enum \| null | sí* | según el tipo (ver diccionario); `null` solo si el resultado no pudo observarse |
| `location` | objeto \| null | no | `{ x, y }` en coordenadas de campo 0..100, solo si el tramo es `field-view` calibrado; `null` en cualquier otro caso |
| `confidence` | number | sí | 0..1 |
| `evidenceClipId` | UUID | sí | |
| `status` | enum | sí | `auto` · `reviewed` · `corrected` · `pending` |
| `notes` | string \| null | no | dudas, desvíos, intenciones no observables |

### 1.5 `Play` — jugada

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `id` | UUID | sí | |
| `matchId` | UUID | sí | |
| `tStart` / `tEnd` | number | sí | `tStart` = inicio del primer evento; `tEnd` = fin del último; `tEnd >= tStart` |
| `teamId` | UUID \| null | sí* | `null` solo con `unknown: true` |
| `period` | string \| null | no | `1st` · `2nd` · `ET1` · `ET2` · `penalties` — solo cuando pueda determinarse |
| `matchClockStart` | string \| null | no | reloj del partido (`MM:SS`), solo si se conoce; nunca sustituye a `tStart` |
| `eventIds` | UUID[] | sí | ordenados por tiempo; mínimo 1 |
| `participants` | UUID[] | sí | jugadores identificados; los desconocidos no se inventan |
| `interpretation` | string \| null | no | explicación táctica; debe distinguirse de los hechos observados |
| `quality` | objeto | sí | `{ coverage: 0..1, uncertainty: string, needsReview: boolean }` |
| `evidenceClipId` | UUID | sí | clip que cubre la jugada completa |
| `status` | enum | sí | `auto` · `reviewed` · `corrected` · `pending` |

### 1.6 `Correction` — corrección del usuario

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `id` | UUID | sí | |
| `targetType` / `targetId` | enum + UUID | sí | `event` · `play` · `player` |
| `field` | string | sí | campo corregido |
| `oldValue` / `newValue` | JSON | sí | |
| `author` | string | sí | |
| `createdAt` | timestamp | sí | |

Las correcciones son **solo de añadido** (append-only): nunca se borra el historial. Corregir un jugador o un evento recalcula las estadísticas dependientes.

### 1.7 `AnalysisJob` — trabajo de análisis

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `id` / `matchId` | UUID | sí | |
| `stage` | enum | sí | `reception` · `preparation` · `segmentation` · `perception` · `tracking` · `calibration` · `events` · `muse-review` · `validation` · `publication` |
| `stageStatus` | enum | sí | `pending` · `running` · `done` · `failed` |
| `progress` | number | sí | 0..100 |
| `error` | string \| null | no | mensaje claro, nunca un código sin explicar |
| `qualityReport` | objeto \| null | no | cobertura, duplicados detectados, casos `pending` |

### 1.8 `QualityReport` — informe de calidad por análisis

| Campo | Tipo | Obligatorio | Reglas |
|---|---|---|---|
| `analyzableSec` / `totalSec` | number | sí | tiempo realmente analizable; el cociente es la cobertura |
| `eventsTotal` / `eventsPending` | number | sí | |
| `playsTotal` / `playsPending` | number | sí | |
| `duplicateEventsRemoved` | number | sí | |
| `identitySwitches` | number | sí | cambios de identidad detectados |
| `processingSec` / `cost` | number \| null | sí* | tiempo y coste medidos; `cost: null` solo si aún no se conoce el precio |

## 2. Ejemplo

```json
{
  "id": "3f9a…",
  "matchId": "7c21…",
  "tStart": 134.20,
  "tEnd": 148.90,
  "teamId": "a1b2…",
  "period": "1st",
  "matchClockStart": "12:34",
  "eventIds": ["e1…", "e2…", "e3…"],
  "participants": ["p11…", "p9…"],
  "interpretation": "Salida corta por la derecha tras recuperación en campo propio.",
  "quality": { "coverage": 0.92, "uncertainty": "El receptor del segundo pase estuvo 1 s ocluido.", "needsReview": true },
  "evidenceClipId": "c55…",
  "status": "pending"
}
```

La interpretación es texto libre con su evidencia; nunca se presenta como hecho observado. El ejemplo usa IDs recortados; en datos reales son UUID completos.

## 3. Reglas de validación (normativas)

- **V-01** `tEnd >= tStart` en eventos, jugadas, segmentos y clips.
- **V-02** Todo `evidenceClipId` referencia un clip existente cuyo rango cubre el evento o la jugada.
- **V-03** Ningún evento tiene `tStart` en un segmento `replay` o `close-up` sin `replayOfEventId` / enlace a su evento original en directo.
- **V-04** `location` solo admite valor cuando el instante pertenece a un segmento `field-view` con calibración válida; en cualquier otro caso es `null`.
- **V-05** `confidence` siempre entre 0 y 1; `confidence < 0.60` obliga a `status: pending`.
- **V-06** Jugador desconocido: `playerIds` sin ese jugador + `unknownPlayers: true`. Prohibido asignar un ID por parecido.
- **V-07** La distancia observada nunca se almacena como distancia total del partido; el campo se llama `observedDistanceM` cuando exista.
- **V-08** Toda corrección conserva `oldValue`; el historial no se reescribe.
- **V-09** `matchClockStart` y `period` son `null` cuando no puedan determinarse; nunca se estiman.
- **V-10** Un `Play` sin `eventIds` (vacío) no se publica.
- **V-11** Los segmentos de un partido no se solapan y cubren el archivo de principio a fin.
- **V-12** `qualityReport.cost` debe rellenarse antes de cerrar el análisis cuando el precio sea conocido; si no lo es, el informe lo dice explícitamente.

## 4. Versionado

Versión del contrato: `0.1.0` (2026-11-06). Cada análisis registra la versión del contrato y del pipeline con la que se produjo. Un cambio de versión exige una entrada en el registro de decisiones del repo.
