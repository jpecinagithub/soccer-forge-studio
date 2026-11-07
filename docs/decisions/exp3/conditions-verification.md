# Experimento 3, parte B — Verificación de condiciones (datos, código, pesos base)

**Fecha de verificación:** 2026-11-07 · **Repo:** `soccer-forge-studio`, rama `main` (base: commit `8f44e84`)
**Alcance:** solo verificación documental (navegación web + lectura de fuentes).
No se ha descargado nada, no se ha entrenado nada, no se ha contratado nada.
B2 no se ha tocado.

Cada entrada indica: fuente, URL, fecha de verificación, qué se verificó y
qué queda pendiente. **Lo no verificado se marca como NO VERIFICADO**; nada
se asume.

---

## 0. Conclusión anticipada: "procedencia limpia" sigue PENDIENTE

La ruta de fine-tuning es **viable como experimento de investigación**, pero
**NO queda establecida como "procedencia limpia"** para ningún uso más allá
de la investigación interna:

1. **Los datos H250 heredan la restricción de SoccerNet: solo investigación,
   sin uso comercial** (FAQ oficial de SoccerNet, verificada 2026-11-07).
   Además, el paper de SoccerNet-v3 dice de los fotogramas/anotaciones v3
   que son descargables "freely, with no restriction whatsoever (open
   licence)", en contradicción aparente con el FAQ. Se adopta la lectura
   estricta (solo investigación) hasta que se aclare.
2. **Los pesos resultantes heredarían AGPL-3.0** por la base YOLOv8n y el
   código de entrenamiento Ultralytics (página oficial de licencias de
   Ultralytics, verificada 2026-11-07: "All Ultralytics YOLO trained models
   fall under the AGPL-3.0 License by default").
3. **Tres cosas quedan NO VERIFICADAS** (ver §§1–3): el campo de licencia
   del registro Zenodo, el contenido del fichero `LICENSE_SoccerNetv3` del
   repo H250, y el contenido del script `train_YOLO_on_SNv3.py` (solo se
   verificó que el fichero existe en el listado del repo).

Consecuencia práctica: los pesos afinados podrán usarse para evaluar dentro
del proyecto (investigación), pero **no** podrán integrarse en un producto
cerrado ni comercial sin resolver (a) la restricción no comercial de
SoccerNet y (b) la licencia Enterprise de Ultralytics (o la publicación del
trabajo derivado completo bajo AGPL-3.0). Esto no es asesoramiento legal.

---

## 1. Datos H250 — SoccerNet_v3_H250

### 1.1 Registro Zenodo (DOI 10.5281/zenodo.7808511)

- **Fuente:** Zenodo, registro 7808511
- **URL:** https://zenodo.org/records/7808511
- **Verificado:** 2026-11-07
- **Verificado:**
  - Publicado el 7 de abril de 2023, versión 1.0, Universidad del Pireo
    (Grecia). Etiqueta "Dataset Open".
  - Descripción: subconjunto de SoccerNet-v3 con los fotogramas en los que
    la altura de la caja de persona no supera 250 px; imágenes PNG
    extraídas y convertidas a JPG; anotaciones filtradas y convertidas a
    formato YOLO. Dos clases: `0` balón, `1` persona (en "person" se
    incluyen las 7 clases humanas de SoccerNet-v3).
  - Particiones preservadas de SoccerNet-v3: **14.368 train / 2.726 val /
    2.692 test** (total 19.786 imágenes).
  - Fichero único: `YOLO.zip`, **2,5 GB, md5 `cdc2401a3275615da894a1b8edfec119`**.
  - Enlaces al código: https://github.com/kmouts/FootAndBall y más info en
    https://github.com/kmouts/SoccerNet_v3_H250.
- **Acceso:** el registro es público y el fichero figura como descargable
  ("Dataset Open"); **no se observó registro, NDA ni aprobación manual**
  en la página del registro. (El NDA de SoccerNet aplica a los **vídeos**
  completos, que H250 no incluye: son fotogramas + anotaciones.)
- **NO VERIFICADO:** el campo de licencia del registro Zenodo no apareció
  en el texto obtenido de la página (ni CC BY ni ninguna otra). No se
  afirma ninguna licencia Zenodo para este registro. Queda pendiente
  comprobar el campo `license` del registro (p. ej. vía la ficha completa
  de Zenodo) antes de afirmar bajo qué licencia se distribuye el ZIP.

### 1.2 Repo https://github.com/kmouts/SoccerNet_v3_H250

- **Fuente:** GitHub, repo público `kmouts/SoccerNet_v3_H250`
- **URL:** https://github.com/kmouts/SoccerNet_v3_H250
- **Verificado:** 2026-11-07 (commit actual `20a99dc3462c5445e4b14f2ebefa06f8fab09846`,
  12 commits, creado 2023-03-23)
- **Verificado:**
  - **Licencia del repo: MIT** (campo License de GitHub: "MIT License").
  - README: "Our code is released under the MIT License (see LICENSE file
    for details). We have added the License from SoccerNet v3."
  - Archivos en la raíz: `images/` (directorio), `LICENSE`, `LICENSE_SoccerNetv3`,
    `README.md`. El repo **NO contiene scripts de entrenamiento ni
    `data.yaml`**: es un repo de documentación/datos (el `images/`
    presumiblemente aloja las figuras del README; no se verificó su
    contenido).
  - Clases confirmadas: solo dos, Ball (0) y Person (1).
  - Cita pedida: Moutselos & Maglogiannis, IISA 2023, DOI
    10.1109/IISA59645.2023.10345947.
- **NO VERIFICADO:** el contenido del fichero `LICENSE_SoccerNetv3`
  (no se pudo leer su texto con las herramientas disponibles). El README
  dice que se añadió la licencia de SoccerNet v3, pero **no se verificó
  qué dice exactamente** (si es el texto de la licencia de SoccerNet-v3,
  un NDA, o una nota). Pendiente de lectura directa antes de citarla.
- **Origen por fotograma / partición por partido:** el repo **no publica**
  una lista de partidos por fotograma ni los splits como ficheros. La
  partición train/val/test **se hereda de SoccerNet-v3** (290/55/55
  partidos según el paper, §2.2 de arXiv:2311.06892), y el paper afirma
  que "the division into training, validation and testing parts has been
  preserved". La estructura de directorios del `YOLO.zip` (no inspeccionada)
  es la única vía para comprobar si el partido de origen es recuperable
  por fotograma. Ver §4 de la receta para la separación que se adopta
  ante esta falta de verificación.

### 1.3 Condiciones de SoccerNet (marco general)

- **Fuente:** SoccerNet FAQ oficial
- **URL:** https://www.soccer-net.org/faq
- **Verificado:** 2026-11-07 (también verificado en el experimento 2)
- **Verificado (citas literales del FAQ):**
  - "Can I use the data from SoccerNet for commercial purposes? **No. The
    SoccerNet dataset is meant for research purposes, it is not intended
    for commercial purposes.** The videos of SoccerNet contains copyright
    that belongs to each European leagues…"
  - "Can I use the algorithms developed by the SoccerNet team for commercial
    purposes? Each algorithm has its own licence…"
  - Los vídeos contienen copyright de las ligas; el NDA es un contrato para
    impedir la redistribución de ese material.
  - Datos actuales en Hugging Face; los conjuntos de **vídeo** son
    restringidos (cuenta HF + aceptación de NDA + aprobación manual).
- **Matiz verificado (paper SoccerNet-v3, Sci. Data 2022, DOI
  10.1038/s41597-022-01469-1, "Usage Notes"):** "Our SoccerNet-v3 dataset,
  as a self-contained dataset of frames and annotation files, is available
  at https://www.soccer-net.org/ and will be downloadable freely, with no
  restriction whatsoever (open licence), as per the fair use principle."
  Y: "Access to the videos is granted to everyone upon filling out a Non
  Disclosure Agreement".
- **Contradicción explícita, sin resolver:** el paper v3 califica los
  fotogramas/anotaciones de "open licence… no restriction whatsoever",
  mientras el FAQ vigente dice que el dataset es solo para investigación
  y no para uso comercial. **No se resuelve aquí.** Se adopta la lectura
  estricta (investigación, no comercial) para cualquier peso entrenado con
  estos datos. Queda pendiente: pedir aclaración o leer el texto de
  `LICENSE_SoccerNetv3` (ver §1.2).

### 1.4 Qué heredarían los pesos del fine-tuning (según lo verificado)

- **De los datos:** restricción a uso de investigación / no comercial
  (FAQ SoccerNet). La calificación "open licence" del paper v3 no se
  traslada automáticamente a los pesos: el FAQ es la condición vigente
  del dataset como conjunto, y los pesos se entrenan con el dataset.
- **De la base y el código (ver §3):** AGPL-3.0 (Ultralytics).
- **Del código kmouts (MIT):** nada restrictivo; la MIT no impone
  condiciones a los pesos.
- **Conclusión:** pesos resultantes = **investigación interna solamente**,
  con doble herencia (no comercial por SoccerNet + copyleft AGPL-3.0 por
  Ultralytics). Cualquier uso comercial o en producto cerrado exige
  resolver ambas. La expresión "procedencia limpia" queda **PENDIENTE**:
  no se usa para estos pesos hasta que se verifiquen el campo de licencia
  de Zenodo (§1.1) y el contenido de `LICENSE_SoccerNetv3` (§1.2), y se
  resuelva la contradicción paper-v3 vs FAQ (§1.3).

---

## 2. Código del repo kmouts

### 2.1 Repo `kmouts/SoccerNet_v3_H250` (datos)

- Ver §1.2. **Contenido exacto verificado:** README + `LICENSE` (MIT) +
  `LICENSE_SoccerNetv3` + directorio `images/`. **No incluye** la receta
  de entrenamiento ni los splits como ficheros ni `data.yaml`. La receta
  vive en el repo hermano (§2.2).

### 2.2 Repo `kmouts/FootAndBall` (código de métodos y métricas)

- **Fuente:** GitHub, repo público `kmouts/FootAndBall` (fork de
  `jac99/FootAndBall` con modificaciones)
- **URL:** https://github.com/kmouts/FootAndBall
- **Verificado:** 2026-11-07 (commit actual
  `2297e61567dedfa53aa2312b9731dcb178f114c7`, 96 commits, rama `master`,
  creado 2022-09-08)
- **Verificado (listado de archivos de la raíz):**
  - **Licencia del repo: MIT** (campo License de GitHub). README: "Our code
    is released under the MIT License (see LICENSE file for details). We
    have added the Licenses from FootAndBall, Ultralytics YOLO 8,
    SoccerNet v3." Ficheros: `LICENSE`, `LICENSE_FootAndBall`,
    `LICENSE_SoccerNetv3`, `LICENSE_Ultralytics_YOLO8`.
  - **Scripts YOLO presentes (existencia verificada por nombre):**
    `train_YOLO_on_SNv3.py`, `predict_with_YOLO_on_SNv3.py`,
    `failed_train_YOLO8n_on_SNv3.py`, `soccernet_v3.yaml`,
    `train_FB_on_SNv3.py`, `train_detector.py`, `run_detector.py`,
    `config.txt`, `configOnSNv3.txt`, `Dockerfile`, `docker-compose.yml`.
  - **Pesos base incluidos en el repo:** `yolov8n.pt` (base COCO sin
    afinar) y `models/` con el `.pth` original de FootAndBall. **No hay
    pesos reentrenados publicados** (confirmado en el experimento 2, §1.3).
  - Entorno declarado en el README: Python 3.8.15, PyTorch 1.13.1,
    Ubuntu 22.04.2 LTS, CUDA 11.6.
  - Estadísticas: `SoccerNetv3_H250_stats.pdf`, `SoccerNetv3_stats.pdf`.
- **NO VERIFICADO — contenido de los scripts:** no se pudo leer el
  contenido de `train_YOLO_on_SNv3.py` ni de `soccernet_v3.yaml` con las
  herramientas disponibles (la página del repo solo expone el listado de
  archivos). Por tanto **no está verificado** que el script contenga la
  receta Ytr1200 tal como la publica el paper (épocas, batch, lr, etc.),
  ni qué rutas/particiones declara el YAML. **Señal de cautela:** existe
  un fichero llamado `failed_train_YOLO8n_on_SNv3.py`, lo que sugiere que
  al menos un intento de entrenamiento YOLO8n sobre SNv3 falló o se
  archivó como fallido; sin leer su contenido no se sabe en qué difiere
  del entrenamiento publicado. La receta de este experimento (§2 del
  informe de receta) se basa en los hiperparámetros **publicados en el
  paper**, no en el contenido no verificado de ese script. Pendiente: leer
  `train_YOLO_on_SNv3.py` y `soccernet_v3.yaml` y conciliarlos con el
  paper antes de ejecutar.
- **NO VERIFICADO — contenido de las licencias añadidas:** el texto de
  `LICENSE_Ultralytics_YOLO8`, `LICENSE_FootAndBall` y
  `LICENSE_SoccerNetv3` dentro de este repo no se leyó. Se asume que
  reproducen las licencias originales; queda pendiente su lectura.

---

## 3. Pesos base YOLOv8n de Ultralytics

- **Fuente:** página oficial de licencias de Ultralytics
- **URL:** https://www.ultralytics.com/license
- **Verificado:** 2026-11-07 (también: Términos de Servicio de Ultralytics,
  https://www.ultralytics.com/legal/terms-of-service, §5)
- **Verificado (citas de la página oficial):**
  - "Ultralytics YOLO models are licensed under AGPL-3.0 by default".
  - "Are Ultralytics YOLO trained models licensed under the AGPL-3.0
    license? **Yes. All Ultralytics YOLO trained models fall under the
    AGPL-3.0 License by default. The AGPL-3.0 License covers the training
    code and the models produced by that training code.**"
  - "If you use Ultralytics YOLO code, models, architectures, training
    pipelines, or trained/fine-tuned models, you must either: Open-source
    your entire project under AGPL-3.0, or; Obtain an Ultralytics
    Enterprise License. This applies even if you: Train your own model
    from scratch; Do not use pretrained weights; Use YOLO only internally
    or for R&D; Deploy through a SaaS platform, API, or other private
    system…"
  - "Using custom-trained or fine-tuned YOLO models in a proprietary or
    commercial setting" es uno de los desencadenantes que exigen licencia
    Enterprise.
  - ToS §5.1: los modelos YOLO se ofrecen bajo dos marcos, (a) uso open
    source bajo AGPL-3.0, (b) uso comercial bajo licencia comercial de
    Ultralytics.
- **Qué heredarían los pesos resultantes:** según Ultralytics, los modelos
  entrenados/afinados con su código caen bajo **AGPL-3.0 por defecto**.
  Un YOLOv8n afinado con H250 heredaría, por tanto, AGPL-3.0 (además de la
  restricción no comercial de SoccerNet, §1.4). Esto no es una
  interpretación: es lo que declara el titular de la licencia. La
  alternativa para uso privativo/comercial es la licencia Enterprise de
  Ultralytics (de pago, precio no verificado; no se ha solicitado).
- **Nota sobre el repo del proyecto:** `soccer-forge-studio` es un repo
  público en GitHub (según memoria del proyecto), pero en su raíz **no se
  observó fichero LICENSE** (listado de `ls -a` del 2026-11-07: sin
  `LICENSE`). La compatibilidad AGPL-3.0 del proyecto como conjunto no
  queda verificada aquí; si los pesos afinados se publicaran como parte
  del proyecto, habría que verificar la licencia del repo y las
  obligaciones de publicación del código correspondiente. Pendiente.

---

## 4. Hiperparámetros publicados de Ytr1200

- **Fuente:** Moutselos & Maglogiannis, "Setting a Baseline for long-shot
  real-time Player and Ball detection in Soccer Videos", arXiv:2311.06892
  (IISA 2023), §II.C y Tabla I.
- **URL:** https://arxiv.org/pdf/2311.06892
- **Verificado:** 2026-11-07 (texto completo del PDF, 6 páginas)

### 4.1 Valores publicados para YOLO8n (Ytr640 / Ytr1200)

| Hiperparámetro | Valor publicado | Fuente en el paper |
|---|---|---|
| Arquitectura / base | YOLO8n (nano, 168 capas, 3.006.038 parámetros), transfer learning desde pesos preentrenados en COCO | §II.B.2, §II.C |
| `imgsz` (entrenamiento) | 1200 (Ytr1200) / 640 (Ytr640) | §II.C |
| Épocas | 100 (máx.), con early stopping | §II.C |
| Paciencia (early stopping) | 5 | §II.C |
| Optimizador | SGD | §II.C |
| Learning rate | `lr = 0.01` | §II.C |
| Batch | AutoBatch: **14** para Ytr1200, 53 para Ytr640 | §II.C |
| Época del mejor modelo (Ytr1200) | **56** (early stopping disparado; se seleccionó el modelo de la época 56) | §II.C |
| Resolución de inferencia (evaluación) | reescalado a 1280×736 y luego a cuadrado 1280×1280 | §II.C |
| Versión Ultralytics | YOLOv8.0.39 | §II.C |
| Hardware / entorno | NVIDIA GeForce RTX 3080, Ubuntu, CUDA 11.6, PyTorch 1.13.1, Python 3.8.15 | §II.C |
| Datos de entrenamiento | Partes train/val de SoccerNet_v3_H250 (14.368 / 2.726); test (2.692) solo para evaluación | §II, §II.A.4 |
| Resultados Ytr1200 (test) | Ball AP11 **0,5361**, Ball COCO mAP 0,2362, Ball Avg Prec 0,877, **Ball Avg Rec 0,707**, Ball % 0,724; Person AP11 0,9058; inferencia 7,4/10,2 ms | Tabla I |

### 4.2 Valores NO publicados para el entrenamiento YOLO

El paper **no publica** para YOLO (sí publica augmentations detalladas
para FootAndBall: CenterCrop 1280×720, ColorJitter, RandomAffine — esas
son de FootAndBall, **no** de YOLO):

- **Augmentations de YOLO:** no publicadas. No se sabe si usaron los
  valores por defecto de Ultralytics 8.0.39 (mosaic, etc.) o una
  configuración propia.
- **Weight decay, momentum, `lrf` (lr final), warmup, scheduler:** no
  publicados.
- **`close_mosaic`, `amp`, `workers`, `seed`:** no publicados.
- **Tiempo de entrenamiento:** no publicado.
- **Tamaño de caja del balón en las anotaciones YOLO:** no publicado
  explícitamente (las anotaciones v3 dan cajas; el paper no detalla
  cómo se convirtió el centro del balón a caja, si se hizo).

La receta (ver `finetune-recipe.md`) toma los valores por defecto de
Ultralytics 8.0.39 para todo lo no publicado y lo declara como tal;
**no se presenta ningún valor por defecto como valor publicado**.
Tras el entrenamiento, los valores efectivos quedan registrados en el
`args.yaml` del run, que es la fuente de verdad.

---

## 5. B1 / B3 (material propio del proyecto)

No son fuentes externas; se recogen aquí solo para fijar qué se verificó
ya en los experimentos 1C/2 y qué papel juegan:

- **B1** (Georgia 0-4 España, 237,24 s, SHA256 `6e7d037e…`): referencia de
  posiciones re-verificada a resolución original (151 filas, 143 V / 8 O),
  con incertidumbre 10–30 px por posición. **Adjudicación humana
  pendiente**; es material exploratorio, no verdad formal.
- **B3** (España 4-0 Bulgaria, 146,72 s, SHA256 `fac63c5c…` verificado):
  referencia de comprobación (138 filas, 74 V / 64 O). Sesgo declarado:
  54 posiciones KEEP derivan del centro de la propuesta YOLO; la
  comparación no sesgada es el subconjunto de 20 V independientes — que
  a su vez es un subconjunto de casos difíciles, no una muestra sin sesgo
  (corrección del usuario, 2026-11-07).
- **B2 sigue reservado: no se ha tocado.**
- Las referencias B1/B3 son **posiciones (puntos)**, no cajas YOLO: no
  sirven como etiquetas de entrenamiento sin una conversión de punto a
  caja que no está definida ni validada. Por eso la receta las usa solo
  para evaluación (ver `finetune-recipe.md`).
- Los clips proceden de la CDN de RFEF (resúmenes oficiales). No se
  verificó su licencia; se usan solo como material de evaluación interna,
  sin redistribución.

---

## 6. Pendientes de verificación (lista cerrada)

1. Campo de licencia del registro Zenodo 7808511 (§1.1).
2. Contenido del fichero `LICENSE_SoccerNetv3` del repo H250 (§1.2).
3. Contenido de `train_YOLO_on_SNv3.py` y `soccernet_v3.yaml` del repo
   `kmouts/FootAndBall`, y conciliación con el paper; en particular qué
   es `failed_train_YOLO8n_on_SNv3.py` (§2.2).
4. Contenido de las licencias añadidas en `kmouts/FootAndBall`
   (`LICENSE_Ultralytics_YOLO8`, `LICENSE_FootAndBall`) (§2.2).
5. Contradicción paper SoccerNet-v3 ("open licence, no restriction
   whatsoever") vs FAQ SoccerNet (solo investigación, no comercial) (§1.3).
6. Licencia del propio repo `soccer-forge-studio` (sin fichero LICENSE en
   la raíz) y sus implicaciones AGPL-3.0 si se publican los pesos (§3).
7. Licencia de los clips RFEF (B1/B3) — solo afecta a la redistribución,
   no al entrenamiento, porque no se entrena con ellos (§5).

Mientras 1, 2 y 5 no se resuelvan, **"procedencia limpia" queda PENDIENTE**
y los pesos resultantes se tratan como **solo investigación, no
comerciales, bajo AGPL-3.0**.
