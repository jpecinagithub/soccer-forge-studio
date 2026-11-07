# Experimento 3 — Receta de fine-tuning YOLOv8n (primera ejecución)

**Fecha:** 2026-11-07 · **Repo:** `soccer-forge-studio`, rama `main`
**Estado:** RECETA PREPARADA, NO EJECUTADA. No se ha entrenado, no se ha
alquilado GPU, no se ha descargado el dataset.
**Base de esta receta:** la configuración publicada de Ytr1200 (Moutselos &
Maglogiannis, arXiv:2311.06892, §II.C y Tabla I). Todo lo no publicado en el
paper se toma de los valores por defecto de Ultralytics YOLOv8.0.39 y se
marca como tal; nada se presenta como publicado si no lo está.
**Condiciones:** ver `conditions-verification.md`. Resumen: datos solo para
investigación (SoccerNet, no comercial) + pesos resultantes bajo AGPL-3.0
(Ultralytics). "Procedencia limpia" PENDIENTE. Los pesos de esta ejecución
son material experimental de investigación, no un artefacto de producto.

**Una sola receta.** No se abre otra comparación de arquitecturas. No se
rediseña el seguimiento (el enlazador sigue congelado; se evalúa solo si la
detección mejora, según el protocolo del experimento 2). B2 sigue reservado.

---

## 1. Objetivo de la ejecución única

Reproducir Ytr1200 (YOLOv8n afinado a 1200 px sobre H250) y medirlo con las
métricas y referencias propias del proyecto (B1 ajuste, B3 comprobación),
en igualdad de condiciones con el candidato 1 del experimento 2.

**Criterio de éxito de la ejecución (se decide después de medir, no antes):**
- (a) Reproduce el orden de magnitud publicado en el test H250: Ball AP11
  ≈ 0,54, Ball Avg Rec ≈ 0,71 (tolerancia de centro 5 px, métrica del
  paper); y
- (b) en B1/B3, a conf 0,25 y tolerancia 50 px, iguala o supera la
  recuperación cruda del candidato 1 (B1 0,748; B3-independiente 0,550)
  **sin** empeorar la tasa de confusiones con el entorno (detecciones en
  fotogramas O y candidatos a error lejos de trayectoria, con la regla
  corregida: precisión solo sobre casos adjudicables, desconocidos aparte).

Si (a) no se reproduce, la primera tarea es diagnosticar la discrepancia
(datos, versión, hiperparámetros), no lanzar una segunda variante.

---

## 2. Datos

### 2.1 Entrenamiento y validación: H250 (única fuente de entrenamiento)

| Conjunto | Imágenes | Uso |
|---|---|---|
| H250 train | 14.368 | Entrenamiento |
| H250 val | 2.726 | Monitorización + early stopping + selección del mejor modelo |
| H250 test | 2.692 | **Solo evaluación final** (métricas del paper). No se entrena con él ni se usa para elegir el modelo. |

- **Origen:** Zenodo DOI 10.5281/zenodo.7808511, `YOLO.zip` (2,5 GB,
  md5 `cdc2401a3275615da894a1b8edfec119`). Descarga libre, sin NDA (los
  vídeos no forman parte de H250). Verificación de integridad obligatoria
  (md5) antes de entrenar.
- **Clases:** 2 — `0 ball`, `1 person` (las 7 clases humanas de
  SoccerNet-v3 consolidadas en `person`, como en el paper). Se mantienen
  las dos clases: es la configuración publicada y la clase `person` da
  contexto para distinguir balón de personas.
- **Formato:** imágenes JPG + etiquetas YOLO normalizadas, tal como vienen
  en el ZIP. No se re-etiqueta nada.
- **Partición:** se usa **tal como la publica H250**, sin remezclar.
  La partición se hereda de SoccerNet-v3 (split por partido 290/55/55);
  ver §5 para el detalle y sus límites.

### 2.2 B1 y B3: solo evaluación, nunca entrenamiento

- **B1 (ajuste, Georgia 0-4 España):** referencia de posiciones
  `docs/decisions/exp2/ball-detector/ref-positions-b1.csv` (151 filas,
  143 V / 8 O). Solo para evaluar la detección cruda del modelo afinado
  con las métricas del experimento 2 (§5–§6 de este documento).
- **B3 (comprobación, España 4-0 Bulgaria):** referencia
  `docs/decisions/exp2/ball-detector/ref-positions-b3.csv` (138 filas,
  74 V / 64 O). Solo para evaluar. La comparación no sesgada usa el
  subconjunto de 20 V independientes de YOLO (y se publica también el
  resultado sobre los 74 V, marcando el sesgo).
- **Por qué no se entrena con B1/B3:** (1) sus referencias son puntos
  (centro del balón), no cajas YOLO; convertir punto→caja exigiría una
  regla no definida ni validada; (2) entrenar con el conjunto de ajuste
  destruiría la separación ajuste/comprobación; (3) B1 es material
  exploratorio con adjudicación humana pendiente.
- **Negativos difíciles de B3** (tambor blanco de grada, logo Halcón,
  botas, postes/red, vallas — exp2 §4.2): se documentan como trabajo
  futuro, **no** se añaden en esta primera ejecución. Añadirlos sería una
  segunda receta, no la reproducción de Ytr1200.

### 2.3 B2: reservado

No se descarga, no se anota, no se evalúa. Reserva para la comparación
final, tras adjudicarlo y fijar configuraciones.

---

## 3. Pesos base

- **Base:** `yolov8n.pt` oficial de Ultralytics (pesos COCO, sin afinar).
  El paper usa transfer learning desde COCO; el repo `kmouts/FootAndBall`
  incluye un `yolov8n.pt` en su raíz, pero la receta descarga el oficial
  de Ultralytics (o usa el que descarga el propio paquete `ultralytics`
  al pedir `yolov8n.pt`) y registra su SHA-256 antes de entrenar.
- **Licencia de la base:** AGPL-3.0; los pesos resultantes heredan
  AGPL-3.0 según Ultralytics (ver `conditions-verification.md` §3).
- **No se usa** el candidato 1 (`bambezius/yolo11n-soccernet-ball`) como
  base ni como inicialización: se conserva solo como resultado comparativo
  ya obtenido. Sus pesos no son dependencia del proyecto.

---

## 4. Hiperparámetros

### 4.1 Publicados en el paper (Ytr1200) — se reproducen tal cual

| Parámetro | Valor | Origen |
|---|---|---|
| `model` | `yolov8n.pt` (COCO) | Paper §II.C |
| `imgsz` | `1200` | Paper §II.C |
| `epochs` | `100` (máx.) | Paper §II.C |
| `patience` | `5` | Paper §II.C |
| `optimizer` | `SGD` | Paper §II.C |
| `lr0` | `0.01` | Paper §II.C |
| `batch` | `14` (fijado explícito; el paper llegó a 14 con AutoBatch en una RTX 3080 de 10 GB) | Paper §II.C |
| `data` | H250 train/val (ver `data.yaml`) | Paper §II |

### 4.2 No publicados — valores por defecto de Ultralytics 8.0.39 (se declaran, no se presentan como publicados)

| Parámetro | Valor adoptado | Nota |
|---|---|---|
| `lrf` | `0.01` | Default 8.0.39 |
| `momentum` | `0.937` | Default 8.0.39 |
| `weight_decay` | `0.0005` | Default 8.0.39 |
| `warmup_epochs` | `3.0` | Default 8.0.39 |
| `warmup_momentum` | `0.8` | Default 8.0.39 |
| `warmup_bias_lr` | `0.1` | Default 8.0.39 |
| `mosaic` | `1.0` (default) | **No publicado**; es el default, no un valor del paper |
| `close_mosaic` | default de la versión instalada | **Registrar el valor efectivo** desde `args.yaml`; el default cambió entre versiones (10 en 8.0.x, 0 en versiones posteriores) — no asumir |
| `amp` | `True` (default) | Mixed precision |
| `workers` | `8` (ajustar a la CPU de la instancia; registrar) | No publicado |
| `seed` | `0` | Fijado para reproducibilidad; no publicado |
| `device` | `0` | Una sola GPU |
| `project` / `name` | `runs/exp3` / `ytr1200-repro` | Nomenclatura del proyecto |
| `save_period` | `-1` (default: solo best/last) | — |
| `val` | `True` (validación cada época, default) | Necesaria para early stopping |

**Regla:** tras el entrenamiento, el `args.yaml` guardado en el directorio
del run es la fuente de verdad de los hiperparámetros efectivos. Si algún
default difiere de lo supuesto arriba, se registra el efectivo y no se
corrige el informe a posteriori.

### 4.3 Versión del software (fijar antes de ejecutar)

- **Objetivo:** `ultralytics==8.0.39` (la versión del paper), Python 3.8.15,
  PyTorch 1.13.1, CUDA 11.6 — el entorno del paper (§II.C).
- **Realidad probable:** 8.0.39 es de 2023; si `pip install
  ultralytics==8.0.39` no resuelve en la imagen de la GPU alquilada, usar
  la versión 8.x más próxima instalable y **registrar la versión exacta
  instalada** (`pip show ultralytics`, `yolo --version`). No mezclar
  versiones entre entrenamiento y evaluación: todo el run (train + val +
  predict sobre B1/B3) con la misma versión instalada.
- El script de preparación (`scripts/exp3-prepare-h250.py`) no instala
  nada; la instalación se hace en la instancia GPU y se registra.

---

## 5. Separación entrenamiento / validación (por partido o secuencia)

### 5.1 Principio

Ningún fotograma vecino —y a ser posible ningún fotograma del mismo
partido— puede estar a la vez en entrenamiento y en validación. La
separación se hace **por partido (o secuencia de origen)**, no por
fotograma aleatorio.

### 5.2 H250: se conserva la partición publicada (sin remezclar)

- H250 publica train/val/test como particiones cerradas (14.368 / 2.726 /
  2.692) heredadas de SoccerNet-v3, cuyo split es **por partido**
  (290 train / 55 val / 55 test, paper §II.A.3). Por construcción de
  SoccerNet-v3, **ningún partido aparece en dos particiones**.
- Por tanto: usar las particiones tal cual **ya es** una separación por
  partido. No se remezcla, no se mueve ningún fotograma entre conjuntos.
- **Límite verificado:** el repo H250 no publica la lista partido→fotograma
  ni los splits como ficheros, y la estructura interna del `YOLO.zip` no
  se ha inspeccionado (ver `conditions-verification.md` §1.2). La
  afirmación "ningún partido en dos particiones" descansa en el paper y
  en la herencia del split de SoccerNet-v3, no en una comprobación propia
  del ZIP. **Comprobación obligatoria antes de entrenar** (parte del
  script de preparación, sin ejecutarla aquí): inspeccionar la estructura
  de directorios del ZIP; si los directorios conservan el identificador
  de partido (o de secuencia) de SoccerNet-v3, verificar mecánicamente
  que ningún identificador aparece en más de una partición y registrar el
  resultado. Si la estructura **no** conserva el origen por fotograma,
  se registra así y la separación descansa únicamente en la partición
  publicada (se acepta, porque re-particionar sin el origen sería peor:
  un reparto aleatorio por fotograma rompería la separación por partido).
- **Regla de no contaminación:** el test H250 (2.692) no se usa para nada
  hasta la evaluación final (§6.2). No se mira, no se valida con él, no
  se elige el modelo con él.

### 5.3 B1 / B3 / B2: separación por partido (propia del proyecto)

| Clip | Partido | Papel | Mezcla con |
|---|---|---|---|
| B1 | Georgia 0-4 España | Ajuste (evaluación) | Ninguna: no se entrena con él |
| B3 | España 4-0 Bulgaria | Comprobación (evaluación) | Ninguna: no se entrena con él |
| B2 | España 2-0 Georgia | **Reservado** | No se toca |

B1 y B3 son partidos distintos entre sí y distintos de los de H250
(SoccerNet-v3 son partidos 2014–2017 de ligas europeas; B1/B3 son
resúmenes RFEF de selecciones 2025). La evaluación sobre B1/B3 es, por
tanto, una comprobación fuera de distribución respecto al entrenamiento,
que es exactamente lo que se quiere medir.

### 5.4 Dentro de B1/B3 (para la evaluación, no para el entrenamiento)

La evaluación usa los tramos ya definidos (B1: S1–S4; B3: C1–C4) con sus
referencias de posiciones. No se mezclan fotogramas entre ajuste y
comprobación: S1+S2 son ajuste y S3+S4 comprobación dentro de B1 (como en
1C), y B3 entera es comprobación. Los cortes entre planos se tratan como
en 1C/2 (reinicio manual documentado; sin automatizar en esta receta).

---

## 6. Comandos exactos

Trabajo previo en la instancia GPU (una sola vez, registrar salidas):

```bash
# 1. Entorno (registrar versiones exactas instaladas)
pip install "ultralytics==8.0.39"  # si no resuelve, versión 8.x instalable más próxima; registrarla
python -c "import torch, ultralytics; print(torch.__version__, ultralytics.__version__)"
nvidia-smi  # registrar GPU, driver, VRAM

# 2. Datos (script del proyecto; descarga + verifica md5 + escribe data.yaml)
python3 scripts/exp3-prepare-h250.py --out data/h250 --verify-md5
#    Comprueba: md5 cdc2401a3275615da894a1b8edfec119, 2,5 GB,
#    conteos 14368/2726/2692, clases {0: ball, 1: person},
#    y (si la estructura lo permite) que ningún partido aparece en dos particiones.
#    Escribe data/h250/data.yaml (ver docs/decisions/exp3/data.yaml como plantilla).
```

Entrenamiento (única ejecución):

```bash
yolo detect train \
  model=yolov8n.pt \
  data=data/h250/data.yaml \
  epochs=100 patience=5 \
  imgsz=1200 batch=14 \
  optimizer=SGD lr0=0.01 \
  lrf=0.01 momentum=0.937 weight_decay=0.0005 \
  warmup_epochs=3.0 warmup_momentum=0.8 warmup_bias_lr=0.1 \
  device=0 workers=8 seed=0 \
  project=runs/exp3 name=ytr1200-repro
```

Equivalente en Python (si el CLI no está disponible en la instancia):

```python
from ultralytics import YOLO
model = YOLO("yolov8n.pt")
model.train(data="data/h250/data.yaml", epochs=100, patience=5,
            imgsz=1200, batch=14, optimizer="SGD", lr0=0.01,
            lrf=0.01, momentum=0.937, weight_decay=0.0005,
            warmup_epochs=3.0, warmup_momentum=0.8, warmup_bias_lr=0.1,
            device=0, workers=8, seed=0,
            project="runs/exp3", name="ytr1200-repro")
```

**Parada:** early stopping con `patience=5` sobre la fitness de validación
(como en el paper; el mejor modelo de Ytr1200 fue el de la época 56).
Máximo 100 épocas. No se reanuda ni se prolonga el entrenamiento después
de la parada: si el resultado no satisface §1, se diagnostica, no se
sigue entrenando a ciegas.

### 6.1 Evaluación en H250 test (métricas del paper)

```bash
yolo detect val model=runs/exp3/ytr1200-repro/weights/best.pt \
  data=data/h250/data.yaml split=test imgsz=1200 batch=1
# Métricas a registrar: mAP50, mAP50-95 por clase; y, con el código de
# métricas de kmouts (FootAndBall) si está disponible, Ball AP11 y Ball
# Avg Rec con tolerancia de centro 5 px (la métrica del paper, Tabla I).
# Si el código de métricas de kmouts no se puede reutilizar tal cual,
# se registra mAP50/mAP50-95 de Ultralytics y se indica explícitamente
# que Ball AP11/Avg Rec (5 px) quedan pendientes de implementar con
# la misma definición del paper — no se improvisan.
```

### 6.2 Evaluación en B1/B3 (métricas del proyecto, comparables con exp2)

Con el mismo `best.pt`, `imgsz 1280`, barrido de confianza post-hoc
0,05/0,10/0,25/0,40/0,60, `iou 0,5`, sobre los fotogramas de referencia de
B1 (S1–S4) y B3 (C1–C4), con los scripts de evaluación del experimento 2
(`scripts/exp2-normalize.py`, `scripts/exp2-evaluate.py`, adaptando solo
la etiqueta de clase `ball` si hace falta):

- Recuperación cruda @50 px por conf; error de localización (mediana/p90)
  **solo en B1** (referencia independiente de ambos detectores).
- Detecciones en fotogramas O y candidatos a error lejos de trayectoria,
  con la **regla corregida** (corrección del usuario, exp2): precisión
  solo sobre casos adjudicables; fotogramas O / no localizables se
  publican aparte, no entran en el denominador de precisión.
- En B3, publicar la comparación sobre los 74 V **y** sobre el subconjunto
  de 20 V independientes; declarar el sesgo en ambos casos.
- El enlazador congelado (g120-c8) solo se aplica si la detección cruda
  mejora según §1(b), y sin tocar sus parámetros.

### 6.3 Artefactos a guardar de la ejecución

- `runs/exp3/ytr1200-repro/weights/best.pt` (+ `last.pt`), `args.yaml`,
  `results.csv`, curvas de entrenamiento.
- SHA-256 de `yolov8n.pt` usado, del `YOLO.zip`, y del `best.pt` resultante.
- Versiones exactas (ultralytics, torch, CUDA, GPU).
- `data/h250/data.yaml` efectivo y el informe de comprobación de la
  separación por partido (§5.2).
- Evaluaciones `eval-b1.json` / `eval-b3.json` en el mismo formato que exp2.
- **Los pesos resultantes se guardan como material experimental de
  investigación** (licencia: AGPL-3.0 + restricción no comercial SoccerNet).
  No se publican como artefacto del producto ni se suben a ningún hub.

---

## 7. Estimación de tiempo de la ejecución única

**El paper no publica la duración del entrenamiento.** La estimación
siguiente es un cálculo explícito con supuestos declarados, no una medida:

- Pasos por época: 14.368 imágenes / batch 14 ≈ **1.026 pasos**.
- Épocas esperadas: el paper paró en la **56** (early stopping); caso
  previsto 56 épocas ≈ **57.500 pasos**; peor caso 100 épocas ≈ 102.600.
- Tiempo por paso: el paper publica 7,4 ms/fotograma de inferencia en
  RTX 3080 (Tabla I). Un paso de entrenamiento (forward + backward +
  optimizador) sobre un batch de 14 se estima en 0,3–0,5 s
  (≈3–5× el coste de inferencia por imagen del batch). De ahí:
  57.500 pasos × 0,3–0,5 s ≈ **4,8–8,0 h en una RTX 3080**.
- En una **RTX 4090** (≈1,5–2× el rendimiento de una 3080):
  **≈2,5–5 h**. En una **A100 80 GB** (batch mayor, p. ej. 32, y más
  rendimiento): **≈2–4 h**.
- Añadir ~1 h de preparación (descarga de 2,5 GB, verificación, entorno)
  y ~0,5 h de evaluaciones. **Total facturable previsto: ~6 h** en la
  opción RTX 4090 (5 h de entrenamiento + 1 h de preparación/evaluación);
  el rango honesto es 4–9 h según GPU y época de parada real.

Si el entrenamiento supera las 100 épocas de tope o el tiempo se desvía
mucho de esta estimación, se registra y se revisa la estimación, no se
cambia la receta a mitad de ejecución.

---

## 8. Opciones de GPU temporal (resumen; detalle en §9)

Verificado 2026-11-07 (precios de terceras fuentes con fecha; los precios
cambian sin aviso — verificar en la página del proveedor antes de
contratar). Coste para **6 h facturables** (estimación §7):

| Opción | GPU recomendada | Precio/h verificado | Coste 6 h | Nota |
|---|---|---|---|---|
| RunPod Secure Cloud | RTX 4090 (24 GB) | $0,89/h | ≈ $5,34 | Pod por segundos; SLA; la más barata con garantías |
| RunPod Community Cloud | RTX 4090 (24 GB) | $0,34/h | ≈ $2,04 | Sin SLA; host tercero |
| Vast.ai (mercado) | RTX 4090 (24 GB) | mediana ~$0,47–0,51/h | ≈ $2,8–3,1 | Precio por oferta; variable por hora |
| Lambda | A10 (24 GB) | $1,29/h | ≈ $7,74 | Sin RTX 4090; A10 ≈ clase 3080 |
| Lambda | RTX A6000 (48 GB) | $1,09/h | ≈ $6,54 | Alternativa con más VRAM (innecesaria aquí) |
| Google Colab Pro | A100 40 GB (si toca) | ~$0,54/h efectivo | $9,99/mes | 100 CU/mes; GPU no garantizada; sin ejecución en segundo plano en Pro |

**Recomendación:** RunPod Secure RTX 4090 (≈$5,3 por la ejecución) como
primera opción: VRAM suficiente (el paper entrenó con 10 GB), precio
verificado, SLA, facturación por segundo. Vast.ai como alternativa más
barata si se acepta la variabilidad del mercado. Colab Pro solo si se
acepta GPU no garantizada y sesión con el navegador abierto (Pro no tiene
ejecución en segundo plano; eso lo tiene Pro+ a $49,99/mes).
Detalle y fuentes en §9.

---

## 9. Opciones de GPU temporal (detalle verificado)

Precios en USD por GPU-hora, on-demand, antes de impuestos, salvo que se
indique lo contrario. **Fuentes de terceros con fecha de lectura** (no se
leyó la página de precios de cada proveedor directamente en todos los
casos; se indica qué se verificó y qué no). Verificar el precio en vivo
antes de contratar.

### 9.1 RunPod (Pods)

- **Precios verificados** (varias fuentes concordantes, lecturas del
  31 oct – 2 nov 2026): RTX 4090 **$0,34/h Community Cloud**,
  **$0,89/h Secure Cloud**; A100 PCIe 80 GB $1,19/h Community / $1,79/h
  Secure; H100 PCIe $1,99/h Community / $2,89/h Secure; H100 SXM $2,69/h
  Community / $3,99/h Secure. Fuentes: stork.ai (precios comprobados en
  runpod.io el 1 nov 2026), promptquorum.com (lectura 2 nov 2026),
  activepieces.com (precios de runpod.io a 31 oct 2026).
- **Advertencia:** una fuente de agosto 2026 daba Secure RTX 4090 a
  $0,69/h; el valor vigente a principios de noviembre es $0,89/h. Los
  precios cambian; la cifra usada aquí es la más reciente verificada.
- Facturación por segundo; almacenamiento aparte. Secure Cloud: centros
  de datos operados por RunPod, con SLA. Community Cloud: hosts terceros,
  sin SLA.
- **Adecuación:** RTX 4090 (24 GB) sobra para batch 14 a imgsz 1200 (el
  paper usó una RTX 3080 de 10 GB). Coste estimado 6 h: **$5,34 (Secure)
  / $2,04 (Community)** + almacenamiento.
- URL: https://runpod.io/pricing (no se abrió directamente en esta
  verificación; precios tomados de las fuentes citadas).

### 9.2 Vast.ai (mercado de ofertas)

- **Precios verificados** (lecturas 3–7 nov 2026): RTX 4090 mediana
  **$0,47/h** (3 nov, Aliteq, lectura de la API de ofertas de Vast) y
  **$0,48–0,51/h típico** (7 nov, aicomputeradar.dev); oferta más barata
  $0,37/h (3 nov); rango del último día $0,34–0,61. A100 mediana ~$0,67–
  $0,83/h según día y variante. H100 desde $1,79/h (oferta más barata,
  3 nov).
- Vast.ai es un mercado: los hosts fijan el precio; varía por hora y por
  oferta. Facturación por segundo mientras corre; almacenamiento aparte;
  ofertas on-demand e interrumpibles (las interrumpibles son más baratas
  pero pueden pararse: **no** usar interrumpible para esta ejecución).
- **Adecuación:** la más barata en mediana; a cambio, fiabilidad variable
  según el host y sin SLA uniforme. Coste estimado 6 h a mediana:
  **≈$2,8–3,1**. Elegir solo ofertas verificadas y on-demand.
- URL: https://vast.ai/pricing (no se abrió directamente; precios tomados
  de Aliteq y aicomputeradar.dev, lecturas 3–7 nov 2026).

### 9.3 Lambda (Lambda GPU Cloud)

- **Precios verificados** (lecturas 6–7 nov 2026, varias fuentes
  concordantes): Quadro RTX 6000 (24 GB) $0,69/h; **RTX A6000 (48 GB)
  $1,09/h**; **A10 (24 GB) $1,29/h**; A100 40 GB $1,99/h; H100 PCIe
  $3,29/h; H100 SXM $4,29/h (1×). Facturación por minuto, sin tasas de
  salida (egress).
- **Lambda no ofrece RTX 4090.** La GPU más cercana a la clase de la
  RTX 3080 del paper es la **A10 (24 GB)** a $1,29/h; la A6000 (48 GB)
  a $1,09/h es más barata y con más VRAM, aunque de generación anterior.
- Coste estimado 6 h: **A10 $7,74; A6000 $6,54**.
- Fuentes: masterprompting.net (precios copiados de lambda.ai/pricing el
  9 oct 2026), nodegrove.io (19 oct 2026), gpurentalprices.com y
  computeprices.com (7 nov 2026).
- URL: https://lambda.ai/pricing (no se abrió directamente).

### 9.4 Google Colab Pro / Pro+

- **Precios verificados** (fastero.com 27 oct 2026; thundercompute.com
  9 oct 2026; gpuperhour.com 21 sep 2026): **Pro $9,99/mes, 100 unidades
  de cómputo (CU)**; **Pro+ $49,99/mes, 600 CU**; pago por uso $9,99 por
  100 CU. Las CU caducan a los 90 días.
- **Coste efectivo por hora (medido por terceros, no publicado por
  Google):** T4 ~1,19 CU/h (≈$0,12/h, ~84 h por 100 CU); **A100 40 GB
  ~5,40 CU/h (≈$0,54/h, ~18 h por 100 CU)**; A100 80 GB ~7,52 CU/h
  (≈$0,75/h, ~13 h por 100 CU). Medición de McCormick, marzo 2026;
  fastero.com advierte de subidas reportadas por usuarios desde el
  29 oct 2026 (≈+20–30 %) sin confirmación de Google.
- **Limitaciones decisivas para esta ejecución:** Google **no garantiza
  ninguna GPU** (puede tocar T4 aunque se pague Pro); sesiones de hasta
  24 h; **Pro no tiene ejecución en segundo plano** (solo Pro+); los
  límites de uso son dinámicos y no se publican. Una ejecución de 3–8 h
  en Pro exigiría mantener el navegador abierto y aceptar que la GPU
  asignada puede no ser una A100.
- Coste: una ejecución de ~5 h en A100 consumiría ~27 CU de las 100
  mensuales (dentro de la suscripción de $9,99), pero la falta de
  garantía de GPU y de ejecución en segundo plano lo hace **no
  recomendable como primera opción**.
- URL: https://colab.research.google.com (precios de la página de registro
  según las fuentes citadas; no se abrió directamente).

### 9.5 No verificadas / descartadas sin verificar

- **AWS / Azure / GCP (p. ej. instancias p4d/g5):** no se verificaron
  precios para esta ejecución; son en general más caras por GPU-hora y
  con más fricción de configuración. No se incluyen en la tabla.
- **Kaggle:** no se verificó la cuota gratuita de GPU ni su adecuación
  (sesiones limitadas, T4/P100). No se incluye.
- **Ultralytics Platform (entrenamiento en la nube):** no se verificó
  precio ni condiciones; además, entrenar allí no cambia las condiciones
  de licencia (AGPL-3.0). No se incluye.
- **Oracle (VM del proyecto):** sin GPU detectada (`nvidia-smi` no
  existe; documentado, no verificado — solo se comprobó la ausencia del
  comando). No es opción.

---

## 10. Qué NO se hace en esta ejecución

- No se entrena con B1, B3 ni B2. No se toca B2.
- No se usa el candidato 1 como base ni como inicialización.
- No se rediseña el seguimiento; el enlazador sigue congelado (g120-c8).
- No se añaden negativos difíciles ni datos propios en esta primera
  ejecución.
- No se cambia ningún hiperparámetro a mitad de ejecución. No se prolonga
  el entrenamiento tras el early stopping.
- No se publica el modelo resultante como artefacto del producto ni se
  sube a ningún hub (condiciones: investigación, AGPL-3.0, no comercial).
- No se contrata ni se ejecuta nada con esta receta: la contratación y la
  ejecución requieren decisión explícita del usuario.

---

## 11. Archivos de esta receta

- `docs/decisions/exp3/finetune-recipe.md` (este archivo).
- `docs/decisions/exp3/conditions-verification.md` (condiciones verificadas
  y pendientes).
- `docs/decisions/exp3/data.yaml` (plantilla; el script escribe la
  versión efectiva con la ruta real de extracción).
- `scripts/exp3-prepare-h250.py` (preparación de datos; sin ejecutar).
