# Experimento 3 — Preparación del fine-tuning de un detector propio de balón

**Fecha:** 2026-11-07 · **Repo:** `soccer-forge-studio`, rama `main` (base `8f44e84`)
**Estado:** PREPARACIÓN COMPLETA, NO EJECUTADA. No se ha entrenado, no se ha
alquilado GPU, no se ha descargado el dataset H250, no se ha rediseñado el
seguimiento. B2 sigue reservado (no se ha tocado).

**Decisión del usuario que enmarca el experimento:** priorizar un detector
propio con procedencia documentada; posponer el rediseño del seguimiento;
conservar el candidato 1 (`bambezius/yolo11n-soccernet-ball`) SOLO como
resultado comparativo ya obtenido — sus pesos NO son una dependencia del
proyecto y el "uso interno" NO resuelve la ausencia de condiciones
explícitas de uso.

**Entregable de este experimento:** receta de entrenamiento reproducible,
condiciones verificadas y evaluación corregida. La ejecución inicial única
vendrá después, con opciones de GPU presentadas para decidir.

## 0. Veredicto

1. **La evaluación está corregida y las tres correcciones del usuario al
   informe exp2 están aplicadas sobre los resultados guardados, sin
   repetir inferencia.** La precisión ya no mezcla casos adjudicables y
   desconocidos; el subconjunto B3-20 queda etiquetado como casos
   difíciles; los "lejos de trayectoria" están verificados visualmente
   uno a uno (10 FP confirmados, 1 balón real).
2. **"Procedencia limpia" sigue PENDIENTE.** La ruta de fine-tuning es
   viable como experimento de investigación, pero los pesos resultantes
   heredarían, según lo verificado, restricción no comercial (SoccerNet)
   + AGPL-3.0 (Ultralytics). Quedan 7 puntos sin verificar (§5).
3. **Hay una única receta reproducible** (YOLOv8n, configuración publicada
   Ytr1200) lista para una sola ejecución inicial, con GPU temporal
   presentada (recomendada: RunPod Secure RTX 4090, ≈ $5,34).
4. **La hipótesis de cajas duplicadas se sostiene** (medición, no nuevo
   seguidor): el candidato 1 pone ≥2 cajas sobre el balón en el 72–84 %
   de los fotogramas V y el enlazador alterna entre ellas. La
   deduplicación previa al enlazador queda como propuesta para decisión
   del usuario, no implementada.

## 1. Parte A — Evaluación corregida (sobre resultados guardados)

Informe completo: `docs/decisions/exp3/exp3-evaluacion-corregida-2026-11-07.md`.
Evaluador nuevo: `scripts/exp3-evaluate.py` (`scripts/exp2-evaluate.py`
intacto; cambio documentado en su cabecera). **Verificación del padre:**
el evaluador se re-ejecutó sobre los resultados guardados y reproduce
**byte a byte** los JSON `eval-corrected-b1.json` y `eval-corrected-b3.json`.

### 1.1 Referencias v3: O → ausente confirmado (A) / no localizable (NL)

Criterio: A = balón demostrablemente fuera del fotograma (p. ej. primeros
planos de celebración); NL = balón en el fotograma — en la red, ocluido en
un scrum, en vuelo — pero posición no determinable de forma fiable.
Decisión por fotograma tras verificación visual (contact sheets + zooms 3×).

| Clip | Antes (v2) | Después (v3) |
|---|---|---|
| B1 | 143 V / 8 O | **145 V / 6 NL / 0 A** |
| B3 | 74 V / 64 O | **76 V / 57 NL / 5 A** (A = 17,0–17,8, celebración) |

Correcciones O→V por verificación visual con zoom 3×: B3 79,6 → V
(935,508); B3 96,4 → V (1135,852); B1 169,4 → V (1040,628); B1 169,6 → V
(980,624). Referencias versionadas:
`docs/decisions/exp3/ref-positions-b1-v3.csv`,
`ref-positions-b3-v3.csv` (columna `o_class`, cambios en `v3_change`).

**Decisión del padre sobre la corrección incidental B1 169,8 — ACEPTADA.**
La posición V (1048,608) se corrigió a (966,609). Verificación
independiente del padre con recortes a resolución original del fotograma
169,8 de B1: el balón (mancha blanca con motion blur) está en (966,609),
junto a la bota rosa del jugador amarillo; la posición antigua cae sobre
el cuerpo del jugador 19 / hierba vacía entre sus piernas. Ambos
detectores coinciden a 1 px en la posición nueva (YOLO (966,610)@0,305;
cand1 (967,609)@0,492) y la trayectoria 169,4 (1040,628) → 169,6 (980,624)
→ 169,8 (966,609) → 170,0 (957,650) es coherente. La corrección queda
registrada en la referencia v3 con su evidencia.

### 1.2 Métricas antes → después (tolerancia 50 px, conf 0,25)

Precisión adjudicable = `tp / (tp + fp_V + fp_A)`; detecciones en
fotogramas NL aparte como desconocidas (no entran en el denominador).
La precisión legacy (definición exp2) se conserva en la salida para el
antes/después.

| | Rec. antes → después | Prec. legacy antes → después | Prec. adjudicable | Desconocidas NL |
|---|---|---|---|---|
| B1 YOLO | 0,455 → **0,462** (67/145) | 0,281 → 0,290 | **0,554** | 0 |
| B1 cand1 | 0,748 → **0,759** (110/145) | 0,296 → 0,305 | **0,582** | 3 dets / 3 fot. |
| B3 YOLO | 0,716 → **0,711** (54/76) | 0,356 → 0,362 | **0,771** | 4 / 3 |
| B3 cand1 | 0,878 → **0,882** (67/76) | 0,269 → 0,277 | **0,713** | 29 / 19 |

Los cambios de recuperación son pequeños y están totalmente explicados por
las correcciones de referencia. El dato que la métrica legacy ocultaba:
B3 cand1 a conf 0,05 dispara **137 detecciones desconocidas en 44
fotogramas NL** — a baja confianza el detector dispara mucho sobre
fotogramas no localizables. La precisión adjudicable es sistemáticamente
mayor que la legacy porque la legacy contaba como FP detecciones en
fotogramas O que ahora son NL (desconocidas) o V.

**Subconjunto B3 (recuperación, tol 50, conf 0,25):** n=20 — YOLO 0,100
(2/20), cand1 **0,550** (11/20) (idéntico a lo publicado en exp2); n=22
(añade los dos V nuevos de exp3, 79,6 y 96,4) — YOLO 0,136, cand1 0,591.
Etiquetado en todos los sitios como **subconjunto útil de casos difíciles,
NO una muestra sin sesgo**.

### 1.3 Candidatos a error lejos de la trayectoria — verificados visualmente

Recomputados desde los JSON normalizados guardados (interpolación lineal
entre V vecinos, ≤1,0 s, mismo segmento; reproduce exp2 §5.3
exactamente). Cada detección verificada con crop 480×480 a resolución
original. **De 11 candidatos, 10 son FP confirmados y 1 es el balón real.**

| Clip | Detector | t | Objeto real | Veredicto |
|---|---|---|---|---|
| B3 | YOLO | 79,6 | Valla publicitaria (borde rojo/blanco del panel F50) | FP |
| B3 | YOLO | 96,4 | Pecho/camiseta de BUL 15 | FP |
| B3 | YOLO | 100,2 | Media verde del portero (BUL 21) ×2 cajas (11 px, mismo objeto) | FP |
| B3 | cand1 | 79,6 | **BALÓN REAL** (939,510)@0,55 — la interpolación falló en un chute en el scrum | TP, no FP |
| B3 | cand1 | 84,2 / 84,4 | Hierba vacía (balón en la red) | FP |
| B3 | cand1 | 84,4 / 84,6 | Bota/media de ESP 8 (×2 cajas en 84,6, 10 px, mismo objeto) | FP |
| B1 | YOLO | 169,6 | Hierba vacía junto a la línea de gol | FP |

Consecuencia: en conf 0,25, los "lejos" de B3 cand1 pasan de 6 a **5 FP
reales**. El caso B3 cand1 79,6 — contado como "lejos de la trayectoria"
en exp2 §5.3 — no era un error del detector sino un fallo de la
interpolación.

### 1.4 Negativos verificados

`docs/decisions/exp3/negatives.csv` — **22 ejemplos**, todos verificados
uno a uno con crop 480×480 2× con cruz en la detección: botas/medias 5,
publicidad/vallas 4, red 3, tambor de grada 3, logos 3, hierba vacía 3,
camiseta 1. **Postes: 0 ejemplos verificables centrados en el poste**
(las cajas del track 3 de 1C están en la zona poste/red pero centradas en
hierba + mota blanca); declarado explícitamente, sin inventar. Los
negativos quedan en el material de desarrollo; **no** se añaden a la
primera ejecución de entrenamiento (la receta reproduce Ytr1200 tal cual;
añadirlos sería una segunda receta).

### 1.5 Muestra de comprobación ciega (B3)

`docs/decisions/exp3/check-sample-b3.csv` +
`check-sample-method.md`. Ventanas elegidas **por tiempo, sin consultar
predicciones** (sondeo a 1 fps, fuera de C1–C4): D1 20,0–23,8 · D2
89,0–92,8 · D3 102,0–105,8 (60 fotogramas a 5 fps). Anotación ciega
(hojas sin cajas) + verificación fotograma a fotograma con zoom 3×.
**Composición: 48 V / 12 NL / 0 A.** Hallazgo metodológico: el grounding a
ciegas NO es fiable sin verificación — solo 3 de 60 puntos estaban
exactos; el resto tenía un desplazamiento sistemático de ~15–110 px y en
4 fotogramas apuntaba a carteles (VALLADOLID/MAPFRE/adidas). La
verificación corrigió 45 posiciones y convirtió 12 fotogramas en NL. La
muestra NO es una muestra sin sesgo del partido (tres ventanas de juego
abierto elegidas por tiempo); no extrapolar sus métricas a todo el
partido. Uso previsto: evaluar el detector afinado con el mismo evaluador
corregido (recuperación sobre los 48 V, detecciones en los 12 NL como
desconocidas aparte).

### 1.6 Hipótesis de cajas duplicadas — SE SOSTIENE

`docs/decisions/exp3/duplicates-analysis.json`. Método: casi-duplicado =
≥2 detecciones cand1 (conf≥0,05) a ≤50 px del balón real en el mismo
fotograma V; cambios de id replicados exactamente según
`exp2-evaluate-linker.py` sobre la referencia v2 (B1 28, B3 14 — coinciden
con los `linker-eval-cand1-*.json` guardados).

- El candidato 1 pone ≥2 cajas SOBRE el balón en el **72 % (103/143)**
  de los fotogramas V de B1 y el **84 % (62/74)** de B3; media 2,85 /
  3,36 cajas sobre el balón por fotograma V (YOLO: 1,36 / 2,04); ≥2 cajas
  fuertes (≥0,25) sobre el balón: 82/143 B1, 60/74 B3.
- En los cambios de id, el id viejo y el nuevo se observan
  SIMULTÁNEAMENTE sobre el balón: mismo fotograma **21/42**, ventana
  ±0,2 s **36/42**. Los cambios oscilan entre los mismos pares de ids
  (3↔4, 4↔6, 1↔2, 6↔9).
- Fotogramas V con ≥2 ids distintos simultáneamente sobre el balón:
  cand1 30/143 B1 (21 %), 16/74 B3 (22 %); control (enlazador YOLO):
  1/143 B1, 0/74 B3, con 2 y 0 cambios de id.
- **Veredicto: la hipótesis se sostiene** — el enlazador mantiene dos
  tracks paralelos sobre el mismo balón alimentados por cajas duplicadas
  y alterna entre ellos. 6/42 cambios no tienen tracks paralelos en
  ventana (otras causas, p. ej. oclusión + re-adquisición como id nuevo).
- La deduplicación previa al enlazador queda como **propuesta para
  decisión del usuario, NO implementada** (fuera de alcance: sin rediseño
  del seguimiento).

**Salvedad:** las métricas del enlazador siguen sobre la referencia v2
(la corrección de 169,8 no se propagó a las métricas del linker). El
error de localización mediano de YOLO en B3 (0,4 px) sigue sin ser
interpretable (la referencia deriva de YOLO por construcción).

## 2. Parte B — Condiciones verificadas

Informe completo: `docs/decisions/exp3/conditions-verification.md`
(cada entrada con fuente, URL, fecha de verificación 2026-11-07, qué se
verificó y qué queda pendiente; lo no verificado se marca como tal).

### 2.1 Datos H250

- **Registro Zenodo** (DOI 10.5281/zenodo.7808511): público, descarga libre
  sin NDA (fotogramas + anotaciones, no vídeos); `YOLO.zip` 2,5 GB, md5
  `cdc2401a3275615da894a1b8edfec119`; particiones **14.368 train / 2.726
  val / 2.692 test**; 2 clases (0 balón, 1 persona). **NO VERIFICADO:** el
  campo de licencia del registro Zenodo no apareció en el texto obtenido.
- **Repo** https://github.com/kmouts/SoccerNet_v3_H250 (commit `20a99dc…`):
  licencia **MIT**; solo README + `LICENSE` + `LICENSE_SoccerNetv3` +
  `images/` — **no** incluye receta ni splits. **NO VERIFICADO:** el
  contenido de `LICENSE_SoccerNetv3`.
- **SoccerNet (marco general)** (FAQ oficial): "The SoccerNet dataset is
  meant for research purposes, it is not intended for commercial
  purposes". **Contradicción sin resolver:** el paper SoccerNet-v3 dice
  de los fotogramas/anotaciones "downloadable freely, with no restriction
  whatsoever (open licence)", mientras el FAQ vigente dice solo
  investigación. Se adopta la lectura estricta (solo investigación).

### 2.2 Código kmouts

- **Repo** `kmouts/FootAndBall` (commit `2297e61…`): licencia **MIT**;
  existen `train_YOLO_on_SNv3.py`, `soccernet_v3.yaml`,
  `predict_with_YOLO_on_SNv3.py` y `yolov8n.pt` (base COCO, sin afinar);
  **no hay pesos reentrenados publicados**. **NO VERIFICADO:** el
  contenido de `train_YOLO_on_SNv3.py` / `soccernet_v3.yaml` (solo se
  verificó que existen por nombre). Señal de cautela: existe un
  `failed_train_YOLO8n_on_SNv3.py` cuyo contenido se desconoce. La receta
  se basa en el paper, no en ese script.

### 2.3 Pesos base YOLOv8n (Ultralytics)

- **Fuente:** https://www.ultralytics.com/license (verificado 2026-11-07).
  "All Ultralytics YOLO trained models fall under the AGPL-3.0 License by
  default" — los modelos entrenados/afinados con su código caen bajo
  **AGPL-3.0 por defecto**; uso privativo/comercial exigiría licencia
  Enterprise. Además: el repo `soccer-forge-studio` no tiene fichero
  `LICENSE` en su raíz (pendiente de verificar).

### 2.4 Qué heredarían los pesos resultantes (según lo verificado)

Pesos resultantes = **solo investigación interna, no comerciales, bajo
AGPL-3.0** (doble herencia: no comercial por SoccerNet + copyleft AGPL-3.0
por Ultralytics). **"Procedencia limpia" queda PENDIENTE** hasta verificar
el campo de licencia de Zenodo (§2.1), el contenido de
`LICENSE_SoccerNetv3` y resolver la contradicción paper-v3 vs FAQ. Esto
no es asesoramiento legal. El candidato 1 no se usa como base en ningún
caso.

### 2.5 Pendientes de verificación (lista cerrada)

1. Campo de licencia del registro Zenodo 7808511.
2. Contenido de `LICENSE_SoccerNetv3` del repo H250.
3. Contenido de `train_YOLO_on_SNv3.py` y `soccernet_v3.yaml`, y
   conciliación con el paper; en particular qué es
   `failed_train_YOLO8n_on_SNv3.py`.
4. Contenido de las licencias añadidas en `kmouts/FootAndBall`
   (`LICENSE_Ultralytics_YOLO8`, `LICENSE_FootAndBall`).
5. Contradicción paper SoccerNet-v3 vs FAQ SoccerNet.
6. Licencia del propio repo `soccer-forge-studio` (sin fichero LICENSE) y
   sus implicaciones AGPL-3.0 si se publican los pesos.
7. Licencia de los clips RFEF (B1/B3) — solo afecta a la redistribución,
   no al entrenamiento, porque no se entrena con ellos.

## 3. Receta de fine-tuning (una única, no ejecutada)

Informe completo: `docs/decisions/exp3/finetune-recipe.md`; plantilla
`docs/decisions/exp3/data.yaml`; preparación
`scripts/exp3-prepare-h250.py` (sintaxis comprobada, **no ejecutado**).
**Verificación del padre:** sintaxis del script comprobada
(`py_compile` OK), incluye verificación md5; `data.yaml` es plantilla
marcada como tal. Corrección aplicada por el padre: la receta atribuía el
"sin GPU" del Oracle al "experimento 3, parte A"; el dato viene de
comprobaciones anteriores (`nvidia-smi` ausente, documentado no
verificado).

- **Objetivo:** reproducir Ytr1200 y medirlo con las métricas propias
  (B1 ajuste, B3 comprobación), en igualdad con el candidato 1.
- **Datos:** solo H250 para entrenar (14.368 train / 2.726 val; test
  2.692 solo evaluación final). B1/B3 solo evaluación (sus referencias
  son puntos, no cajas YOLO; entrenar con B1 destruiría la separación
  ajuste/comprobación). B2 reservado.
- **Base:** `yolov8n.pt` oficial de Ultralytics (COCO). El candidato 1
  no es base ni inicialización.
- **Hiperparámetros publicados de Ytr1200** (verificados en
  arXiv:2311.06892, §II.C y Tabla I): YOLO8n desde COCO, `imgsz 1200`,
  100 épocas máx., `patience 5`, SGD `lr=0.01`, batch 14 (AutoBatch en
  RTX 3080), mejor modelo época 56; resultados test: Ball AP11 **0,5361**,
  Avg Rec **0,707**. **No publicados:** augmentations de YOLO, weight
  decay, momentum, `lrf`, warmup, `close_mosaic`, `amp`, `seed`, tiempo
  de entrenamiento — la receta usa los defaults de Ultralytics 8.0.39
  para todo eso y lo declara como tal (con `args.yaml` del run como
  fuente de verdad).
- **Comando:** `yolo detect train model=yolov8n.pt
  data=data/h250/data.yaml epochs=100 patience=5 imgsz=1200 batch=14
  optimizer=SGD lr0=0.01 … project=runs/exp3 name=ytr1200-repro`
  (equivalente Python incluido en la receta).
- **Parada:** early stopping `patience=5` (el paper paró en la época 56);
  sin reanudar ni prolongar.
- **Éxito (se decide después de medir):** (a) reproducir Ball AP11 ≈0,54
  / Avg Rec ≈0,71 en test H250 (tolerancia 5 px); y (b) en B1/B3, a conf
  0,25 y tol 50 px, igualar o superar la recuperación cruda del candidato
  1 (B1 0,748; B3-independiente 0,550) **sin** empeorar la tasa de
  confusiones (con la regla corregida: precisión solo sobre adjudicables,
  desconocidos aparte). Si (a) no se reproduce, diagnosticar antes que
  lanzar otra variante.
- **Evaluación:** H250 test con métricas del paper + B1/B3 con las
  métricas de exp2 (rec@50, barrido conf 0,05–0,60, precisión corregida);
  el enlazador congelado (g120-c8) solo se aplica si la detección cruda
  mejora, sin tocar sus parámetros.

### 3.1 Separación entrenamiento / validación (por partido o secuencia)

- **H250:** se conserva la partición publicada sin remezclar — es ya una
  separación por partido porque hereda el split por partido de
  SoccerNet-v3 (290/55/55). **Comprobación obligatoria antes de
  entrenar** (parte del script de preparación): si la estructura del ZIP
  conserva el identificador de partido, verificar mecánicamente que
  ningún identificador aparece en más de una partición; si no lo
  conserva, se registra así y la separación descansa únicamente en la
  partición publicada (re-particionar sin el origen sería peor). El test
  H250 (2.692) no se usa para nada hasta la evaluación final.
- **B1/B3/B2:** partidos distintos entre sí y fuera de H250 (SoccerNet-v3
  son partidos 2014–2017 de ligas europeas; B1/B3 son resúmenes RFEF de
  selecciones 2025). B1 = ajuste (evaluación), B3 = comprobación
  (evaluación), B2 = reservado.

## 4. GPU temporal — una única ejecución (sin contratar)

Estimación de tiempo (cálculo explícito, no medida; el paper no publica
duración): 14.368/14 ≈ 1.026 pasos/época × 56 épocas ≈ 57.500 pasos; a
0,3–0,5 s/paso ≈ **4,8–8,0 h en RTX 3080**, **≈2,5–5 h en RTX 4090**,
**≈2–4 h en A100**; +~1 h de preparación/evaluación → **~6 h facturables**
como cifra de trabajo (rango honesto 4–9 h). VRAM: basta 24 GB (el paper
entrenó con 10 GB).

| Opción | GPU | Precio/h verificado | Coste ~6 h |
|---|---|---|---|
| **RunPod Secure Cloud (recomendada)** | RTX 4090 24 GB | $0,89 (1–2 nov 2026, fuentes terceras) | **≈ $5,34** |
| RunPod Community Cloud | RTX 4090 24 GB | $0,34 (1–2 nov 2026) | ≈ $2,04 |
| Vast.ai (mercado) | RTX 4090 24 GB | mediana ~$0,47–0,51 (3–7 nov 2026) | ≈ $2,8–3,1 |
| Lambda | A10 24 GB | $1,29 (6–7 nov 2026) | ≈ $7,74 |
| Lambda | RTX A6000 48 GB | $1,09 (6–7 nov 2026) | ≈ $6,54 |
| Google Colab Pro | A100 40 GB (si toca) | ~$0,54/h efectivo; $9,99/mes | $9,99/mes |

Colab Pro queda como no recomendada como primera opción: GPU no
garantizada y sin ejecución en segundo plano en Pro (eso es Pro+,
$49,99/mes). **No verificado:** precios de AWS/Azure/GCP, Kaggle y
Ultralytics Platform (no incluidos); las páginas de precios de los
proveedores no se abrieron directamente en todos los casos — los precios
son de fuentes terceras fechadas y **deben re-verificarse en vivo antes de
contratar**. Nada contratado ni ejecutado. Oracle no es opción (sin GPU
detectada).

## 5. Archivos producidos

| Archivo | Contenido |
|---|---|
| `docs/decisions/exp3-finetune-prep-2026-11-07.md` | Este informe |
| `docs/decisions/exp3/exp3-evaluacion-corregida-2026-11-07.md` | Informe parte A (evaluación corregida) |
| `docs/decisions/exp3/conditions-verification.md` | Condiciones verificadas y pendientes (parte B) |
| `docs/decisions/exp3/finetune-recipe.md` | Receta única de fine-tuning (parte B) |
| `docs/decisions/exp3/data.yaml` | Plantilla data.yaml H250 |
| `docs/decisions/exp3/ref-positions-b1-v3.csv` | Referencia B1 v3 (145 V / 6 NL / 0 A) |
| `docs/decisions/exp3/ref-positions-b3-v3.csv` | Referencia B3 v3 (76 V / 57 NL / 5 A) |
| `docs/decisions/exp3/eval-corrected-b1.json` | Métricas corregidas B1 |
| `docs/decisions/exp3/eval-corrected-b3.json` | Métricas corregidas B3 + subconjuntos 20/22 |
| `docs/decisions/exp3/negatives.csv` | 22 negativos verificados (postes: 0) |
| `docs/decisions/exp3/check-sample-b3.csv` | Muestra ciega B3 (60 fot.: 48 V / 12 NL) |
| `docs/decisions/exp3/check-sample-method.md` | Método de la muestra ciega |
| `docs/decisions/exp3/duplicates-analysis.json` | Análisis de duplicados (veredicto: se sostiene) |
| `scripts/exp3-evaluate.py` | Evaluador corregido (nuevo; exp2 intacto) |
| `scripts/exp3-prepare-h250.py` | Preparación de datos H250 (sin ejecutar) |

## 6. Lo que NO se hizo (y qué falta para ejecutar)

- No se entrenó, no se descargó H250, no se alquiló GPU, no se rediseñó
  el seguimiento, no se tocó B2, no se usó el candidato 1 como base.
- Para la ejecución inicial única falta la decisión del usuario sobre la
  GPU (opciones en §4) y, si se quiere resolver antes, las 7
  verificaciones pendientes de §2.5 (la 1, 2 y 5 son las que mantienen
  "procedencia limpia" en PENDIENTE).
- La deduplicación previa al enlazador es una propuesta sin implementar;
  su decisión es del usuario.
- Los pesos resultantes, si se entrenan, serán material experimental de
  investigación (no comercial, AGPL-3.0); no se publican como artefacto
  del producto ni se suben a ningún hub.
