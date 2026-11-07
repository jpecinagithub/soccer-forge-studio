# Experimento 2 — Selección de un detector especializado de balón

**Fecha:** 2026-11-07 · **Repo:** `soccer-forge-studio`, rama `main`
**Estado:** COMPLETADO (candidatos, referencia, detección cruda y enlazador congelado)

## Correcciones del usuario (2026-11-07, sobre este informe)

- **La precisión mezcla detecciones evaluables y desconocidas.** Las
  detecciones en fotogramas O entran en el denominador de precisión aunque
  no se cuenten como falsos positivos. Si no sabemos dónde está el balón,
  no podemos penalizar automáticamente esas detecciones. Separar visible,
  ausente confirmado y no localizable; calcular precisión solo sobre casos
  adjudicables y publicar los desconocidos aparte. (Corrección aplicable
  sobre los resultados guardados, sin repetir inferencia.)
- **Los 20 fotogramas de B3 no son una muestra completamente
  independiente.** Sus coordenadas se corrigieron sin aceptar directamente
  la propuesta de YOLO, pero parte de su selección procede precisamente de
  fallos o ausencias de YOLO. Es un subconjunto útil de casos difíciles,
  no una comparación sin sesgo del partido completo.
- **Alejarse de una trayectoria interpolada no demuestra un falso
  positivo.** La interpolación ya falló con golpeos y cambios de cámara.
  Esos casos deben llamarse candidatos a error hasta comprobar visualmente
  qué objeto detectan.

## 0. Veredicto

**El candidato 1 (`bambezius/yolo11n-soccernet-ball`, YOLO11n afinado en SoccerNet-v3)
recupera el balón mucho mejor que el YOLO genérico, pero NO demuestra menos
confusiones entre balón y objetos del entorno.** La mejora es de recuperación,
no de limpieza:

| Métrica (conf 0,25, tol 50 px) | YOLO genérico | Candidato 1 |
|---|---|---|
| Recuperación cruda B1 (ref. independiente, n=143 V) | 0,455 | **0,748** |
| Recuperación cruda B3 (n=74 V) | 0,716 | **0,878** |
| Recuperación B3 en V independientes de YOLO (n=20) | 0,100 | **0,550** |
| Precisión cruda B1 / B3 | 0,281 / 0,356 | 0,296 / 0,269 |
| | *(mezcla casos evaluables y desconocidos; pendiente de recalcular solo
sobre casos adjudicables, ver correcciones)* | |
| Error de localización mediano B1 | 15,4 px | 16,0 px |
| Detecciones en fotogramas O, B3 (conf 0,25) | 8 | 35 |
| De ellas, lejos de la trayectoria (>100 px, candidatos a error) | 4 | 6 |
| Velocidad (Oracle, CPU) | ~28× real | **~9–12× real** |

Con el **enlazador CONGELADO de 1C (g120-c8)**:

| Track rec@50 | YOLO+enlazador | Cand1+enlazador |
|---|---|---|
| B1 ajuste (S1+S2, n=73 V) | 0,438 | **0,644** |
| B1 comprobación (S3+S4, n=70 V) | 0,343 | **0,629** |
| B3 (n=74 V) | 0,716* | **0,838** |

| Tasa de error (solo-equivocado) | YOLO+enlazador | Cand1+enlazador |
|---|---|---|
| B1 ajuste | 0,123 | 0,219 |
| B1 comprobación | 0,243 | 0,200 |
| B3 | 0,054* | 0,108 |

| Fragmentación (cambios de id) | YOLO+enlazador | Cand1+enlazador |
|---|---|---|
| B1 (ajuste+comprobación) | 2 | **28** |
| B3 | 0 | **14** |

\* B3 está sesgado a favor de YOLO: la referencia B3 deriva de sus propuestas
(§4.3). La comparación no sesgada en B3 es el subconjunto V independiente.

**Consecuencias:**
1. **El candidato 1 se conserva como resultado comparativo ya obtenido**
   para seguir experimentando (recupera el balón en muchos más fotogramas,
   con la misma precisión de localización y 3× más rápido). **NO se integra
   como artefacto del proyecto: no declara licencia** (§1.1). El "uso
   interno" no resuelve la ausencia de condiciones explícitas de uso; sus
   pesos no se convierten en una dependencia del proyecto.
2. **El enlazador es ahora el cuello de botella, no el detector.** Con el
   candidato 1 el enlazador congelado sigue el balón en más fotogramas, pero
   fragmenta mucho más (28 cambios de id frente a 2 en B1) y su tasa de
   trayectorias equivocadas no baja (0,210 global en B1 frente a 0,182 de
   YOLO). No se reajusta (protocolo); el siguiente paso es rediseñar el
   seguimiento o usar las detecciones crudas como señal principal, decisión
   del usuario (§7).
3. **El candidato 2 (FootAndBall original) queda descartado como detector
   directo** para retransmisiones: su resultado publicado en test de
   retransmisión es Avg Rec 0,022 (§1.2). Es código de referencia, no un
   detector usable.
4. **Ruta de fine-tuning limpia** (sin ejecutar): receta kmouts/H250, YOLO
   afinado en fotogramas SoccerNet-v3 H250 (§1.4, §7.2).

---

## 1. Candidatos

Máximo dos, con pesos disponibles, procedencia de entrenamiento, licencia y
código de inferencia documentados. Cada dato verificado en su fuente.

### 1.1 Candidato 1 — `bambezius/yolo11n-soccernet-ball` (probado primero)

- **Página:** https://huggingface.co/bambezius/yolo11n-soccernet-ball
  (verificado vía API de Hugging Face, 2026-11-07).
- **Qué es:** YOLO11n afinado para detección de balón con anotaciones
  SoccerNet-v3. Una sola clase: `ball` (verificado por inspección del
  modelo en Oracle: `names: {0: 'ball'}`).
- **Pesos:** `best.pt`, **10.827.727 bytes**, SHA-256
  `9f1ac6034e06b2430df3c2e6fdb77c69898416a0c9ed6cb74228fd701a20ec88`
  (verificado: el fichero descargado en Oracle coincide exactamente con el
  `checkpoint-info.json` del repo). Repo público, no restringido, 93
  descargas, creado 2026-09-05.
- **Entrenamiento (según `checkpoint-info.json` y `args.yaml`, verificados):**
  mejor época 31, fitness 0,52262; base `yolo11n.pt`; `data:
  artifacts/yolo11-soccernet-data/data.yaml` (**no publicado en el repo:
  clases y particiones no verificables de forma independiente**); 50 épocas,
  batch 48, `imgsz: 1280`, optimizador SGD, GPU RTX 5090.
  `results.csv` **termina en la época 20** mientras `best.pt` es de la época
  31: las métricas de la época 31 no son auditables desde él. Época 20
  (validación, 3.136 fotogramas): precisión 0,816, recuperación 0,754,
  mAP50 0,809, mAP50-95 0,510; error de centro media 19,48 px, mediana
  1,36 px (media ≫ mediana: hay valores atípicos — FP o cajas mal centradas).
- **Licencia: NINGUNA declarada** (`cardData` sin campo de licencia). El
  README dice: "Private copy of a checkpoint fine-tuned for ball detection
  using the glitch project and SoccerNet-v3 annotations" y "This is a model
  transfer, not a grant of additional rights to the upstream model or
  training dataset. Refer to Ultralytics and SoccerNet's applicable terms."
  La base YOLO11 es AGPL-3.0; los datos SoccerNet son solo para
  investigación. **Consecuencia: experimento interno solamente; no integrar
  como artefacto del proyecto sin resolver la licencia.**
- **Código de entrenamiento:** el enlace
  https://github.com/anthonyceponis/glitch **devuelve HTTP 404 (verificado)**:
  el código de entrenamiento no es verificable.
- **Inferencia:** `ultralytics.YOLO("models/yolo11-soccernet/best.pt")`,
  estándar Ultralytics.

### 1.2 Candidato 2 — FootAndBall original (`jac99/FootAndBall`)

- **Repo:** https://github.com/jac99/FootAndBall · **Licencia MIT verificada**
  vía API de GitHub (SPDX MIT, Copyright (c) 2020 Sport Algoritmics and
  Gaming). Paper arXiv:1912.05445 (Komorowski, Kurzejamski, Sarwas).
- **Pesos:** `models/model_20201019_1416_final.pth`, **825.503 bytes**, git
  blob SHA `368ef2805765681c01c5687edb3f3c7ee8414a22` (el origen no publica
  SHA-256). **FootAndBall NO es de Cioppa y NO está entrenado en SoccerNet**
  (Cioppa es autor de SoccerNet, no de FootAndBall).
- **Entrenamiento:** ISSIA-CNR (6 vídeos Full-HD de cámara fija, 20.000
  fotogramas, anotaciones semiautomáticas con errores documentados) +
  SoccerPlayerDetection (2.019 imágenes, **sin anotación de balón**: el balón
  se entrena solo con ISSIA).
- **Salida:** mapa de confianza (ancho/4 × alto/4) cuyo máximo es la posición
  del balón: **punto + confianza, no caja ajustada** (la verdad de ISSIA para
  el balón es solo el centro x,y). Inferencia `run_detector.py` (vídeo →
  vídeo anotado; `--ball_threshold`/`--player_threshold`, por defecto 0,7).
  `torch.load` sin `weights_only` (pickle antiguo): cargar solo ese fichero
  de confianza.
- **Resultado publicado decisivo** (Moutselos & Maglogiannis 2023,
  arXiv:2311.06892, Tabla I, verificado en el PDF): en test de retransmisión
  SoccerNet_v3_H250, pesos originales (FBo): Ball AP11 **0,0096**, Avg Prec
  0,783, **Avg Rec 0,022**, Ball % 0,234 (TP = centro predicho a ≤5 px del
  centro real). FootAndBall reentrenado (FBtr): Avg Rec 0,678 — **pero esos
  pesos reentrenados no están publicados**. YOLO8n afinado a 1200 px
  (Ytr1200): Ball AP11 0,5361, Avg Rec 0,707.
- **Veredicto:** arquitectura y código de referencia, **no un detector
  directo para B1**. No se ejecutó (el dato publicado ya lo descarta para
  retransmisiones).

### 1.3 Rechazados (con motivo)

- **SoccerNet sn-gamestate / baseline GSR** (GPL-3.0): el detector es un
  YOLOv8 genérico sin afinar; GSR reconstruye solo deportistas — **el balón
  no forma parte de la tarea ni de la salida**.
- **SoccerNet Ball Action Spotting** (incl. FOOTPASS/TAAD): localiza
  **acciones en el tiempo**, no la posición del balón en cada imagen
  (distinto por definición; ver §2).
- **kmouts/FootAndBall + SoccerNet_v3_H250**: solo receta — `models/` contiene
  únicamente el `.pth` original y `yolov8n.pt` es la base COCO sin afinar;
  **no hay pesos reentrenados publicados**. Es la ruta de fine-tuning
  recomendada, no un candidato (§1.4).
- **Adit-jain/soccana** (YOLO11n, pesos existentes, 990 descargas): sin
  licencia declarada, dataset "multi-source" sin procedencia precisa, balón
  1 de 3 clases, sin métricas específicas de balón.
- **aabyzov/easychamp-player-detection-yolov8**: "custom soccer match
  videos", sin procedencia ni licencia.
- **Roboflow Universe** como clase (p. ej. `DFL Soccer Ball Detection`
  checkpoint `COCOn` = base COCO sin afinar; `soccer_ball` 1.884 imágenes;
  `Soccer Balls Caltech 256` 287 fotos fijas): datasets CC BY 4.0 pero
  modelos sin descripción, métricas de balón ni descarga de pesos verificada.
- **Ganador GSR 2024** (Constructor Tech YOLO-X + Deep-EIoU + OSNet): sin
  pesos públicos localizados.
- **DeepBall**: predecesor de FootAndBall, superado, no verificado por
  separado.

### 1.4 Ruta de fine-tuning (sin ejecutar)

Si no hay pesos adecuados y verificables, la ruta limpia es afinar YOLO con
datos de fútbol (kmouts/H250):
- **Datos:** SoccerNet-v3 H250 (Moutselos et al.): solo planos largos
  (altura máxima de jugador ≤250 px), 2 clases (0 balón, 1 persona),
  particiones **14.368 train / 2.726 val / 2.692 test**; código en
  https://github.com/kmouts/SoccerNet_v3_H250, Zenodo
  10.5281/zenodo.7808511.
- **Resultado publicado de referencia:** YOLO8n afinado a 1200 px: Ball AP11
  0,5361, Avg Rec 0,707 (frente a 0,0096 / 0,022 del FootAndBall original).
- **Condición:** los datos SoccerNet son solo para investigación (ver §2);
  los pesos resultantes heredan esa restricción. Requiere GPU temporal (el
  Oracle no tiene GPU verificada). Propuesta detallada en §7.2.

## 2. SoccerNet: acceso, condiciones y la distinción clave

Verificado en https://www.soccer-net.org/faq (2026-11-07):

- "Can I use the data from SoccerNet for commercial purposes? **No. The
  SoccerNet dataset is meant for research purposes**"; los vídeos tienen
  copyright de las ligas europeas y el NDA impide la redistribución; "Each
  algorithm has its own licence".
- Los datos están ahora en Hugging Face; los conjuntos de **vídeo** son
  restringidos (cuenta HF + aceptación de NDA + aprobación manual).
- Matiz: el paper SoccerNet-v3 (Sci. Data 2022) indica que los fotogramas y
  anotaciones v3 se descargan libremente "with no restriction whatsoever
  (open licence)"; la parte restringida con NDA son los **vídeos completos**.
  La ruta H250 usa fotogramas/anotaciones v3, así que el fine-tuning propio
  es viable sin acceso a los vídeos.

**Ball Action Spotting ≠ localización del balón por fotograma.**
Ball Action Spotting localiza **acciones** (pase, tiro, etc.) en el tiempo:
dada una secuencia, dice *cuándo* ocurre una acción. No dice *dónde está el
balón en cada imagen*. Son tareas distintas por definición: una es
clasificación temporal de acciones, la otra es detección/localización
espacial por fotograma. Ningún resultado de Ball Action Spotting (FOOTPASS,
TAAD u otros) demuestra capacidad de localizar el balón en cada imagen, y
este experimento evalúa solo eso.

## 3. Conjuntos: B1 ajuste, B3 comprobación, B2 reservado

- **B1 (ajuste):** Georgia 0-4 España, RFEF, 237,24 s, 1920×1080, 25 fps,
  SHA256 `6e7d037e15e72407c20609db3ed5758f0b265c5e1514514a50414bd74e5d55d6`
  (verificado 2026-11-06). Anotación v2 exploratoria (8 jugadas, 11 eventos,
  5 puntuables); adjudicación humana pendiente.
- **B3 (comprobación):** España 4-0 Bulgaria, RFEF, **146,72 s**, 1920×1080,
  25 fps, H.264 + AAC, 361.069.010 bytes, SHA256
  `fac63c5c999a7fb61c809737ce6f5b478f6d77d32c378fb3980ade7a323dcc30`
  (**verificado: coincidencia exacta** con `data/clips/SHA256.json`).
  Descargado de la URL CDN de RFEF en
  `data/clips/espana-bulgaria-rfef.info.json`
  (`https://rfef-ondemand.flumotion.com/outgoing/video/mp4/high/resumen-espan-a-bulgaria-68eed7c7.mp4`),
  como se descargó B1.
- **B2 (España 2-0 Georgia) sigue reservado: no se ha tocado.**

Tramos de comprobación B3 (vista de campo, comprobados visualmente a 5 fps
y por análisis de diferencia de fotogramas; los cortes se hallaron por
inspección — la detección de escenas de ffmpeg no detecta cortes entre
planos verdes similares):

| Tramo | Rango | Duración | Contenido |
|---|---|---|---|
| C1 | 10,0–18,0 s | 8,0 s | Ataque ancho continuo; gol ~13,4 s; celebración/pr. plano desde ~17,0 |
| C2 | 53,4–59,4 s | 6,0 s | Ataque tras primer plano de red; segundo gol ~56–57 s |
| C3 | 77,8–85,8 s | 8,0 s | Ataque ancho continuo; gol ~84,4–84,8 s |
| C4 | 95,2–100,8 s | 5,6 s | Plano trasero de portería, seguimiento prieto del gol (caso duro: balón junto a red, portero en el suelo, congestión) |

Total: **27,6 s → 138 fotogramas a 5 fps**. Segmentos cortados sin
recompresión (libx264 crf 0, sin audio) en `data/clips/work/exp2/b3-seg/`; la
identidad de píxeles se verificó a +4,0 s frente al original (md5 PNG igual
en los 4).

## 4. Referencia fiable (antes de ejecutar los detectores)

### 4.1 B1: re-verificación a resolución original

Base: referencia de 1C (`data/clips/work/exp1c/ref-positions.csv`, 151
fotogramas a 5 fps, V=145, O=6; coordenadas ya en 1920×1080 pero anotadas
desde celdas de 960×540, con ruido residual ~40 px). Método, en orden:
hojas de verificación 480×480 a resolución original (13 hojas, cruz en la
posición 1C) → 28 posiciones marcadas → zooms 3× (240×240, rejilla cada 40
px originales) → recortes anchos 480×480 (2×) donde el balón no estaba en
el zoom → zooms 3× de confirmación centrados en las posiciones corregidas
para los casos ambiguos de S2b → revisión de los 6 fotogramas O a plena
resolución.

**Lecciones de método (para el informe y para futuros trabajos):**
1. La prueba de desviación del punto medio de la trayectoria no es fiable
   para un balón chutado a 5 fps: los chutes crean esquinas genuinas que se
   marcan como errores. No usarla para validar posiciones.
2. Las lecturas de hoja (1×) tienen ruido; corregir solo desplazamientos
   >40 px desde hojas, y verificar con zoom 3×.
3. Los recortes anchos (2×) pueden engañar: las medias blancas se confunden
   repetidamente con el balón; el zoom 3× es el árbitro.
4. Las correcciones pequeñas (10–30 px) leídas solo de hoja están dentro
   del ruido de lectura: no aplicarlas; conservar la posición 1C y asignar
   incertidumbre por contexto.

**Error propio, hallado y corregido en esta sesión:** el CSV de correcciones
contenía inicialmente valores (fantasma) de x_1c/y_1c inventados para 25
filas de S4 (197,0–201,8), escritos de memoria en vez de leídos de
`ref-positions.csv`. Consecuencia: las primeras hojas de zoom de S4 estaban
centradas en posiciones erróneas (las cruces caían en la grada / en las
vallas publicitarias; ese "hallazgo" era MI error, no un error de 1C). La
auditoría contra el CSV verdadero encontró las 25 discrepancias; el CSV se
corrigió a los valores verdaderos y las hojas se regeneraron con centros
correctos. Regla: leer siempre las coordenadas del CSV fuente, nunca de
memoria; auditar antes de verificar.

**Referencia B1 final** (`data/clips/work/exp2/ref-positions-b1.csv`,
copia versionada en `docs/decisions/exp2/ball-detector/`): **151 filas,
143 V / 8 O** (antes 145 V / 6 O). Composición: 120 conservadas de 1C,
**21 corregidas (media 68,5 px, máx. 143 px)**, 2 V nuevas, 4 O nuevas,
4 O originales confirmadas. Incertidumbre sobre V: 10 px: 22, 15 px: 28,
20 px: 39, 25 px: 32, 30 px: 22. Correcciones ≥100 px: 170,8 (105), 195,2
(103), 198,6 (109), 199,2 (143), 200,6 (113): confirman que la referencia
1C tenía errores sustanciales en congestión y en la secuencia de gol, como
advirtió el usuario. Limitación: las 117 posiciones correctas en hoja (1×)
no se verificaron con zoom; su incertidumbre (10–25 px por contexto) lo
refleja. Pueden quedar errores <~25 px en algunas, dentro de la tolerancia
de evaluación de 50 px.

### 4.2 B3: anotación de comprobación

88 fotogramas con propuesta YOLO (hojas 480×480 a resolución original, cruz
en la propuesta) + 50 sin propuesta (hojas de fotograma completo 960×540).
Verificación 3× de las 88 propuestas: **KEEP 54, CORRECT 3, FP 30,
INCERTIDUMBRE 1**. Por tramo: c1 12 KEEP / 3 FP; c2 3 KEEP / 11 FP /
1 INCERTIDUMBRE; c3 21 KEEP / 1 CORRECT / 10 FP; c4 18 KEEP / 2 CORRECT /
6 FP. Correcciones: 78,2 → (1100,563); 96,8 → (1015,866);
100,6 → (17,400) (corrige la lectura wide (10,400); ver §4.4).

Los 31 fotogramas FP/INCERTIDUMBRE se resolvieron todos (fotograma completo
+ zoom 3× en posiciones interpoladas + recortes anchos 2× + zooms 3× de
confirmación): **V = 8** (56,0 (1233,337); 78,4 (976,502); 78,6 (914,483);
79,4 (774,527); 83,6 (322,533); 84,8 (557,393); 99,6 (338,352);
100,6 (17,400)); **O = 23**. Los 13 fotogramas sin propuesta interpolables
se verificaron con zoom 3×: 10 V, 3 O. Los 37 fotogramas sin propuesta
restantes se resolvieron con las hojas de fotograma completo: todos O
(balón en la red no localizable, o primer plano de celebración sin balón en
el fotograma), incluidos los 4 de vuelo (13,6, 13,8, 84,4, 100,0) verificados
con zoom 3× sobre la trayectoria estimada: ninguno mostró el balón de forma
fiable.

**Patrones de FP de YOLO (los negativos difíciles, el objeto del
experimento):** tambor blanco redondo de la grada (repetido: 57,2, 57,8,
58,0 c2; 83,6, 84,2, 84,8 c3); logo de marca de la valla Halcón (54,4, 55,4,
55,8 c2); vallas/mayordomo (55,0, 56,0, 56,2 c2; 78,4, 78, 6, 79,4, 79,6 c3);
grada (54,8, 84,6, 85,6); valla oscura (78,4, 78,6 c3); hierba/línea vacía
(57,4 c2, 81,8 c3, 95,2, 97,4 c4); media/pierna del portero (99,6, 100,2,
100,4 c4; 14,4 c1); espalda/pecho de jugador (14,2 c1, 96,4 c4). En juego
abierto las propuestas YOLO son precisas (los 12 fotogramas de ataque C1
10,4–13,4 KEEP a ~10 px; C3 77,8–84,0 casi todos KEEP; C4 balón grande casi
todos KEEP). Los FP se concentran donde la cámara abandona el juego vivo:
momentos de gol, planos de grada/celebración y secuelas con el portero en
el suelo.

**Lecciones de método (B3):**
1. Las lecturas de recorte ancho (2×) para balón en vuelo/gol NO son
   fiables: camisetas/caras de aficionados, medias, líneas, nudos de red y
   logos de valla se leyeron repetidamente como balón (14,2, 14,4, 54,8,
   55,8, 59,2, 99,6); el zoom 3× es el árbitro.
2. **Un balón en la red tras la malla, con grada detrás, a menudo NO es
   localizable de forma fiable ni a plena resolución con zoom** → O es la
   decisión honesta (14,2/14,4/15,4, 57,2–58,0, 59,2, 84,2/84,6/85,6,
   100,2/100,4).
3. La interpolación lineal falla en pases y cortes/paneos de cámara
   (desviaciones 35–121 px); el zoom es el árbitro.
4. **Recorte de zoom cerca de los bordes:** cuando el centro pedido está
   cerca de un borde (x<120), el recorte se fija y la cruz marca el centro
   del recorte, no el centro pedido (100,6: etiqueta (10,320), cruz en
   (120,320)); leer las posiciones desde el origen del recorte, no desde la
   cruz.

**Referencia B3 final** (`data/clips/work/exp2/ref-positions-b3.csv`,
copia versionada en `docs/decisions/exp2/ball-detector/`): **138 filas,
74 V / 64 O**. V por tramo: c3 31, c4 22, c1 15, c2 6. O por tramo: c1 25,
c2 24, c3 9, c4 6. Incertidumbre sobre V: 10 px: 53, 15 px: 15, 20 px: 4,
25 px: 2.

**Referencia combinada** (`data/clips/work/exp2/ref-positions.csv`, copia
versionada): 289 filas (151 B1 + 138 B3), con columna `clip` y registro de
origen por fila (`source`).

### 4.3 Sesgo conocido de la referencia B3 (declarado)

Las posiciones de referencia de los 54 fotogramas KEEP son **el centro de
la propuesta YOLO, aceptado tras verificación visual 3×**. Por tanto:
- El **error de localización de YOLO en B3 es ~0 por construcción** (mediana
  0,4 px) y no es interpretable; el del candidato 1 se mide contra una
  referencia derivada de YOLO. La comparación de localización válida es la
  de B1 (referencia independiente de ambos detectores).
- La **recuperación de YOLO en B3 está inflada** en esos 54 fotogramas (la
  referencia ES su detección). La comparación en B3 es el subconjunto de
  20 fotogramas V independientes de YOLO (3 CORRECT +
  7 resueltos desde FP + 10 interpolados): YOLO 0,100 frente a candidato 1
  0,550 a conf 0,25 (§5). **Ese subconjunto no es una muestra
  completamente independiente:** sus coordenadas se corrigieron sin
  aceptar directamente la propuesta de YOLO, pero parte de su selección
  procede de fallos o ausencias de YOLO. Es un subconjunto útil de casos
  difíciles, no una comparación sin sesgo del partido completo.
- El enlazador YOLO en B3 hereda el mismo sesgo (§6).

## 5. Detección cruda (sin seguidor)

Configuración común: `imgsz 1280`, `conf 0,05` (barrido post-hoc
0,05/0,10/0,25/0,40/0,60), `iou 0,5`, CPU Oracle (sin GPU). YOLO genérico:
`yolov8s.pt`, ultralytics 8.4.204, torch 2.15.0+cpu, clases [0,32].
Candidato 1: `best.pt` (bambezius), mismas versiones, clase [0] (`ball`).
Scripts: `scripts/exp2-cand1-predict.py` (igual que 1B salvo las etiquetas,
que se toman de `model.names`), `scripts/exp2-normalize.py`,
`scripts/exp2-evaluate.py`. Archivos en
`docs/decisions/exp2/ball-detector/` (`pred1280-*.json`, `cand1-*.json`,
`norm-*.json`, `eval-b1.json`, `eval-b3.json`).

### 5.1 Velocidad y volumen

- YOLO B3: 690 fotogramas en 773,7 s de pared (~28× real; c1 27,54×, c2
  27,83×, c3 28,45×, c4 28,35×).
- Candidato 1: B1 s1 11,77×, s2 9,59×, s3 8,73×, s4 8,55×; B3 c2 8,38×, c3
  8,41×, c4 9,02×. **~9–12× real, 2,4–3,3× más rápido que YOLO a 1280.**
  Ambos muy por encima del objetivo de rendimiento ≤3× (ahora objetivo, no
  corte). Coste de API: 0 (proceso local).
- Detecciones de balón a conf 0,05 en la parrilla de referencia: B1 YOLO 707,
  cand1 710; B3 YOLO 409, cand1 471. El candidato 1 emite a menudo **cajas
  casi duplicadas del mismo balón** (p. ej. dos cajas a conf 0,635 y 0,052
  en el mismo balón): la NMS no las fusiona; esto alimenta la fragmentación
  del enlazador (§6).

### 5.2 Recuperación y precisión (tolerancia principal 50 px)

| | B1 (n=143 V) | | B3 (n=74 V) | |
|---|---|---|---|---|
| conf | YOLO rec / prec | Cand1 rec / prec | YOLO rec / prec | Cand1 rec / prec |
| 0,05 | 0,580 / 0,117 | **0,797 / 0,161** | 0,797 / 0,144 | **0,892 / 0,140** |
| 0,10 | 0,566 / 0,179 | **0,783 / 0,234** | 0,797 / 0,225 | **0,878 / 0,211** |
| 0,25 | 0,455 / 0,281 | **0,748 / 0,296** | 0,716 / 0,356 | **0,878 / 0,269** |
| 0,40 | 0,371 / 0,381 | **0,678 / 0,319** | 0,595 / 0,404 | **0,851 / 0,310** |
| 0,60 | 0,203 / 0,630 | **0,413 / 0,415** | 0,392 / 0,382 | **0,568 / 0,372** |

- **El candidato 1 recupera mucho más balón en todos los umbrales y en los
  dos partidos.** A recuperación comparable, su precisión es mejor en B1
  (a rec ~0,58, cand1 prec ~0,35 frente a 0,117 de YOLO) y comparable en B3.
- **Subconjunto B3 independiente de YOLO (n=20 V):** a conf 0,25, YOLO
  0,100 (2/20), candidato 1 **0,550 (11/20)**; a conf 0,05, YOLO 0,250,
  candidato 1 0,600. Es la evidencia menos sesgada de la mejora.
- **Error de localización (B1, referencia independiente):** a conf 0,25,
  YOLO mediana 15,4 px / p90 38,1 px; candidato 1 mediana 16,0 px / p90
  42,5 px. **Comparable.** (B3: YOLO 0,4 px por construcción, no
  interpretable; candidato 1 1,0 px contra referencia derivada de YOLO.)

### 5.3 Falsos positivos y confusiones con el entorno

El evaluador cuenta FP solo en fotogramas V; se hizo un conteo suplementario
en fotogramas O (donde el balón está ausente o no es localizable) y un
análisis de proximidad a la trayectoria interpolada.

**Detecciones en fotogramas O (B3, 64 fotogramas O):**

| conf | YOLO total (/fotograma O) | Cand1 total (/fotograma O) |
|---|---|---|
| 0,05 | 91 (1,42) | 154 (2,41) |
| 0,10 | 35 (0,55) | 79 (1,23) |
| 0,25 | 8 (0,13) | 35 (0,55) |
| 0,40 | 3 (0,05) | 12 (0,19) |
| 0,60 | 3 (0,05) | 3 (0,05) |

El conteo bruto en O es mayor para el candidato 1, **pero está confundido**:
muchos fotogramas O contienen el balón en la red (presente pero no
localizable para la referencia), así que una detección ahí puede ser el balón
real. El proxy más limpio es la distancia a la trayectoria interpolada
(≤1 s entre V vecinos; >100 px = confusión clara):

| B3, conf 0,25 | cerca de trayectoria (≤100 px) | lejos (>100 px) | sin interpolación* |
|---|---|---|---|
| YOLO (8 dets) | 3 | **4** | 1 |
| Cand1 (35 dets) | 7 | **6** | 22 |

\* Sin interpolación: tramos de celebración (C1 14,0–17,8, C2 57,0–59,0)
sin V vecinos en ≤1 s; el balón está en la red o fuera de plano. No
clasificables por trayectoria.

A conf 0,40: YOLO 0 lejos, candidato 1 1 lejos (79,6 (939,510), conf 0,55).
En B1 (solo 8 fotogramas O): a conf 0,25, YOLO 2 dets (1 lejos), candidato 1
9 dets (0 lejos, 8 cerca de trayectoria).

**Lectura honesta:** el candidato 1 NO demuestra menos confusiones en
número absoluto — produce más detecciones en fotogramas O — pero los
candidatos a error lejos de la trayectoria son **similares en número**
(6 frente a 4 a conf 0,25 en B3; 0 frente a 1 en B1), mientras recupera
mucho más balón. Alejarse de una trayectoria interpolada **no demuestra**
un falso positivo (la interpolación ya falló con golpeos y cambios de
cámara): esos casos son candidatos a error hasta comprobar visualmente qué
objeto detectan. La mejora es de recuperación a tasa de confusión por
detección similar, no de limpieza.

## 6. Enlazador congelado de 1C (g120-c8)

Protocolo: solo si la detección mejora. La detección mejora en recuperación
(§5), así que se aplicó el enlazador **sin tocarlo**: `gate_min 120,
gate_max 200, gate_k 2,0, coast_max 8`, Kalman CV fijo, reinicios manuales
en los cortes (B1: s2 134,6, s3 164,8; B3: ninguno, tramos continuos).
El enlazador filtra por `cls == "sports ball"`, así que las predicciones
del candidato 1 se alimentaron mediante copias con la etiqueta renombrada
(`ball` → `sports ball`); el código del enlazador no se modificó.
Script de evaluación: `scripts/exp2-evaluate-linker.py` (réplica las
métricas de 1C). Para comparar en igualdad, el enlazador YOLO de 1C se
**re-evaluó sobre la referencia B1 corregida** (los números de 1C usaban la
referencia antigua); el enlazador YOLO sobre B3 se ejecutó ahora con la
misma configuración congelada.

### 6.1 Recuperación de track (solo posiciones OBSERVADAS, tol 50 px)

| | B1 ajuste (n=73 V) | B1 comprobación (n=70 V) | B3 (n=74 V) |
|---|---|---|---|
| YOLO+enlazador | 0,438 | 0,343 | 0,716* |
| Cand1+enlazador | **0,644** | **0,629** | **0,838** |

El enlazador sigue el balón en muchos más fotogramas con el candidato 1.
Hueco máximo: B1 YOLO 2,0/3,0 s, candidato 1 1,0/1,0 s; B3 YOLO 0,6 s,
candidato 1 0,4 s. Fotogramas V sin ningún track: B1 YOLO 32/29, candidato 1
10/12; B3 YOLO 17, candidato 1 4.

### 6.2 Trayectorias equivocadas y fragmentación

| Tasa de error (solo-equivocado) | B1 ajuste | B1 comprobación | B3 |
|---|---|---|---|
| YOLO+enlazador | 0,123 (9/73) | 0,243 (17/70) | 0,054* (4/74) |
| Cand1+enlazador | 0,219 (16/73) | 0,200 (14/70) | 0,108 (8/74) |

Global B1: YOLO 0,182 (26/143), candidato 1 0,210 (30/143). **La tasa de
trayectorias equivocadas no baja; en global es ligeramente mayor.**
Fotogramas con track correcto Y equivocado a la vez: B1 YOLO 2/10, candidato 1
2/2; B3 YOLO 9, candidato 1 0.

**Fragmentación (cambios de id entre fotogramas V correctos consecutivos):**
B1 YOLO 0/2, candidato 1 **18/10**; B3 YOLO 0, candidato 1 **14**.
N.º de tracks: B1 YOLO 14/21, candidato 1 20/28; B3 YOLO 20, candidato 1 30.
El enlazador con el candidato 1 pierde y re-adquiere el balón mucho más a
menudo, y cambia de identidad en ~23–38 % de los fotogramas correctos
(frente a 0–8 % con YOLO). Mecanismo probable: las cajas casi duplicadas del
candidato 1 (§5.1) se tratan como objetos distintos y el enlazador salta
entre ellas; además, la mayor densidad de detecciones ofrece más candidatos
para iniciar tracks nuevos. No se ha verificado visualmente track a track;
es una hipótesis, no un hecho.

Caveat: la tasa de error depende de qué fotogramas son V frente a O. La
referencia nueva marca más fotogramas de congestión como O que la antigua,
así que los valores absolutos no son comparables con el 0,41 de 1C en
comprobación; la comparación YOLO–candidato 1 sobre la misma referencia
nueva sí es válida. Y B3 está sesgado a favor de YOLO (§4.3).

### 6.3 Lectura

El candidato 1 + enlazador congelado **sigue el balón en más fotogramas y
con huecos más cortos, pero no disminuye las trayectorias equivocadas y
fragmenta mucho más**. El criterio del protocolo ("menos confusiones entre
balón y objetos del entorno; una trayectoria más larga NO es mejora si sigue
el objeto equivocado") **no se cumple en su forma estricta**: la trayectoria
es más larga Y más completa, pero no más limpia. El cuello de botella ya no
es la detección del balón: es el seguimiento.

## 7. Decisión y próximos pasos

### 7.1 Decisión

1. **Candidato 1 como línea base de detección para seguir experimentando.**
   Recupera el balón mucho mejor, localiza igual de bien y es 3× más rápido.
   **No se integra como artefacto del proyecto** (sin licencia declarada;
   uso interno de experimentación solamente).
2. **Candidato 2 descartado** como detector directo (dato publicado: Avg Rec
   0,022 en retransmisión).
3. **El enlazador congelado no se reajusta.** Su fragmentación con el
   candidato 1 y su tasa de error sin mejorar indican que el siguiente paso
   es un rediseño del seguimiento (o prescindir de él y trabajar sobre
   detecciones crudas), no afinar g120-c8.
4. **B2 sigue reservado** para la comparación final, tras adjudicarlo y
   fijar configuraciones.

### 7.2 Propuesta de fine-tuning (sin ejecutar)

Si la licencia del candidato 1 no se resuelve, o si se quiere un detector
propio con procedencia limpia:
- **Datos:** SoccerNet-v3 H250 (fotogramas + anotaciones, acceso libre según
  el paper v3; vídeos no necesarios). 14.368 train / 2.726 val / 2.692 test,
  2 clases (balón, persona), solo planos largos. Código y particiones en
  https://github.com/kmouts/SoccerNet_v3_H250 (Zenodo
  10.5281/zenodo.7808511). **Condición: datos solo para investigación; los
  pesos resultantes heredan esa restricción.**
- **Base:** YOLO11n o YOLOv8n (la receta publicada usa YOLO8n a 1200 px:
  Ball AP11 0,5361, Avg Rec 0,707). `imgsz` 1200–1280, como el candidato 1.
- **GPU:** temporal (alquiler por horas o servicio con GPU); el Oracle no
  tiene GPU verificada. Estimar coste y tiempo antes de ejecutar; no se ha
  pedido presupuesto (el presupuesto no es criterio de corte, pero se mide
  e informa).
- **Evaluación:** la misma referencia de este experimento (B1 ajuste, B3
  comprobación, B2 reservado) y las mismas métricas (§5–§6), para comparar
  en igualdad con el candidato 1.
- **Antes de ejecutar:** confirmar acceso a H250 y sus condiciones exactas,
  y decidir la base (YOLO11n frente a YOLOv8n) con el usuario.

### 7.3 Preguntas para el usuario (decisión suya)

- ¿Se acepta el candidato 1 como línea base de detección pese a la licencia
  no declarada (solo experimentación interna), o se prioriza la ruta de
  fine-tuning con procedencia limpia?
- ¿Siguiente paso: rediseñar el seguimiento (el enlazador congelado
  fragmenta con detecciones densas), o trabajar sobre detecciones crudas del
  candidato 1 y posponer el seguimiento?

## 8. Reproducibilidad

**Referencias** (copias versionadas en `docs/decisions/exp2/ball-detector/`):
`ref-positions-b1.csv` (151 filas, 143 V / 8 O),
`ref-positions-b3.csv` (138 filas, 74 V / 64 O),
`ref-positions.csv` (289 filas, combinada con columna `clip`).
Originales de trabajo (no en Git, gitignored) en `data/clips/work/exp2/`.

**Predicciones** (en `docs/decisions/exp2/ball-detector/`):
- YOLO: `pred1280-s{1..4}.json` (de 1B) y `pred1280-c{1..4}.json`
  (ejecutados en Oracle 2026-11-07, `exp2/runs.log`).
- Candidato 1: `cand1-{s1..s4,c1..c4}.json` (Oracle, `exp2/cand1-runs.log`;
  pesos verificados SHA-256 `9f1ac603…20ec88`).
- Normalizadas: `norm-yolo-b1.json`, `norm-cand1-b1.json`,
  `norm-yolo-b3.json`, `norm-cand1-b3.json`.
- Evaluaciones: `eval-b1.json`, `eval-b3.json`.

**Enlazador** (en `docs/decisions/exp2/ball-detector/linker/`):
`link-cand1-{s1..s4,c1..c4}-g120-c8.json`,
`link-yolo-{c1..c4}-g120-c8.json` (YOLO B1 en `docs/decisions/exp1c/`);
evaluaciones `linker-eval-*.json`.

**Scripts** (`scripts/`, nuevos en este experimento):
`exp2-verify-ref.py`, `exp2-b3-crops.py`, `exp2-evaluate.py`,
`exp2-zoom-verify.py`, `exp2-wide-verify.py` (específico de B1, rutas
fijas; NO usar para B3), `exp2-confirm-zoom.py`, `exp2-cand1-predict.py`,
`exp2-normalize.py`, `exp2-b3-zoom.py` (genérico; también hace recortes
anchos 2× con `--size 480 --scale 2`), `exp2-b3-full.py`,
`exp2-evaluate-linker.py`.

**Comandos clave:**
```
# candidato 1 (Oracle): scripts/exp2-cand1-predict.py, imgsz 1280, conf 0.05
# normalizar + evaluar (detección cruda):
python3 scripts/exp2-normalize.py --pred docs/decisions/exp2/ball-detector/cand1-s1.json ... \
  --ref data/clips/work/exp2/ref-positions-b1.csv --ball-cls ball \
  --detector cand1-yolo11n-soccernet --out docs/decisions/exp2/ball-detector/norm-cand1-b1.json
python3 scripts/exp2-evaluate.py --ref data/clips/work/exp2/ref-positions-b1.csv \
  --det docs/decisions/exp2/ball-detector/norm-yolo-b1.json \
  --det docs/decisions/exp2/ball-detector/norm-cand1-b1.json \
  --out docs/decisions/exp2/ball-detector/eval-b1.json
# enlazador congelado (g120-c8; el enlazador filtra cls == "sports ball",
# por eso las predicciones del candidato 1 se renombran ball -> sports ball):
python3 scripts/exp1c-linker.py --pred data/clips/work/exp2/cand1-s1-as-sportsball.json \
  --seg s1 --out docs/decisions/exp2/ball-detector/linker/link-cand1-s1-g120-c8.json \
  --gate-min 120 --gate-max 200 --gate-k 2.0 --coast-max 8 --reset-at ""
```

**Notas de método que condicionan los números:**
- B3: referencia derivada en parte de propuestas YOLO (§4.3); la
  localización de YOLO en B3 es 0 por construcción y su recuperación está
  inflada; usar el subconjunto independiente (n=20) para la comparación
  no sesgada.
- El evaluador de detección (`exp2-evaluate.py`) no cuenta detecciones en
  fotogramas O como FP en `fp_dets` (sí entran en el denominador de
  precisión); el conteo suplementario en O está en §5.3. **Defecto
  conocido, pendiente de corregir:** la precisión así calculada mezcla
  casos evaluables y desconocidos; debe calcularse solo sobre casos
  adjudicables, con los desconocidos publicados aparte (ver correcciones).
- La tasa de error del enlazador depende de qué fotogramas son V frente a
  O; no comparar sus valores absolutos con los de 1C (referencia distinta).
- La referencia B1 re-verificada tiene incertidumbre 10–30 px por posición;
  errores <~25 px pueden quedar en las 117 posiciones verificadas solo a
  1×, dentro de la tolerancia de 50 px.
