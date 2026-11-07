# Experimento 3, parte A — Correcciones de evaluación sobre resultados guardados

**Fecha:** 2026-11-07 · **Repo:** `soccer-forge-studio`, rama `main` (base `8f44e84`) ·
**Alcance:** SOLO resultados guardados. Sin inferencia repetida, sin entrenamiento, sin
rediseño del seguimiento, sin tocar B2 (reservado). Sin commit ni push (el padre verifica
y commitea).

**Responde a:** correcciones del usuario al informe exp2 (2026-11-07):
(1) la precisión mezclaba casos adjudicables y desconocidos — separar visible /
ausente-confirmado / no-localizable, precisión solo sobre adjudicables, desconocidos aparte;
(2) los 20 fotogramas V independientes de B3 son un subconjunto útil de casos difíciles,
NO una muestra sin sesgo; (3) la distancia a la trayectoria interpolada NO demuestra un FP —
esos casos son *candidatos* a error hasta verificar visualmente qué objeto detectan.

## 1a. Separación O → ausente confirmado (A) / no localizable (NL) y correcciones de referencia

**Criterio.** A = balón demostrablemente fuera del fotograma (p. ej. primeros planos de
celebración). NL = balón en el fotograma — en la red, ocluido en un scrum, en vuelo — pero
posición no determinable de forma fiable. Decisión por fotograma tras verificación visual:
contact sheets de todos los O de B1 y de los O ambiguos de B3 + zooms 3× (240×240)
centrados en la posición interpolada.

**Conteos v3** (referencias `ref-positions-{b1,b3}-v3.csv`, columna `o_class`, cambios en
`v3_change` con evidencia en `note`):

| Clip | Antes (v2) | Después (v3) |
|---|---|---|
| B1 | 143 V / 8 O | **145 V / 6 NL / 0 A** |
| B3 | 74 V / 64 O | **76 V / 57 NL / 5 A** (A = 17,0; 17,2; 17,4; 17,6; 17,8 — celebración, verificado a 17,0 y 17,8) |

**Correcciones O→V encontradas por la verificación visual obligatoria:**

| Fotograma | Nueva posición | Evidencia |
|---|---|---|
| B3 79,6 | V (935,508), unc 15 | Balón claro en zoom 3× centrado en la det. cand1 (939,510)@0,55; el veredicto O de exp2 usó una ventana centrada en la interpolación (800,516) que falló el balón por ~130 px (cambio rápido de dirección en el scrum) |
| B3 96,4 | V (1135,852), unc 20 | Balón claro en zoom 3× centrado en la interpolación (1148,860), en la bota del tirador, parcialmente tras la media roja; YOLO (1127,850)@0,18 y cand1 (1129,859)@0,57 coinciden |
| B1 169,4 | V (1040,628), unc 15 | Balón claro en zoom 3× en el pie del jugador amarillo; YOLO (1042,626)@0,252, cand1 (1042,626)@0,585 |
| B1 169,6 | V (980,624), unc 25 | Balón como mancha horizontal con motion blur, centro ±20 px; trayectoria 169,4 → 169,6 → 169,8 corregido coherente; cand1 (989,624)@0,49 |
| B1 169,8 | V corregido (1048,608) → **(966,609)**, unc 25 | Corrección incidental V→V (fuera del alcance estricto de 1a; el padre decide aceptarla o revertirla): la posición antigua caía en hierba vacía entre las piernas del jugador; el balón es la mancha blanca en (966,609), donde YOLO (966,610)@0,305 y cand1 (967,609)@0,492 coinciden; coherente con 169,6 (980,624) y 170,0 (957,650) |

B3 97,4 se mantiene O/NL (zoom 3× en la interpolación muestra solo pierna; en (1100,770) hay
un fragmento blanco/azul tras la pierna del tirador, no distinguible balón vs bota blanca;
las cajas cand1 ahí (1097,768)@0,137 quedan como desconocidas, no como FP). Los demás O
de B1 (70,8; 138,8; 139,6; 140,4; 194,0; 199,0) son NL verificados por zoom.

## 1b. Subconjunto B3 de 20 fotogramas V independientes

Reconstruido exactamente (n=20) desde `b3-zoom-verdicts.csv` + `b3-interp.csv`:
10,2; 11,0; 11,4; 54,0; 54,2; 56,0; 78,2; 78,4; 78,6; 79,4; 81,2; 81,4; 81,6; 82,4; 83,6;
84,8; 96,8; 97,2; 99,6; 100,6 (3 CORRECT + 7 resueltos desde FP + 10 V interpolados).
**Etiquetado en todos los sitios como «subconjunto útil de casos difíciles, NO una muestra
sin sesgo».** Subconjunto extendido n=22 añade los dos fotogramas V de exp3 (79,6 y 96,4).
Resultados en `eval-corrected-b3.json` (`subset_independent`, `subset_independent_ext`).

## 1c. Candidatos a error lejos de la trayectoria interpolada — verificados visualmente

Recomputados desde los JSON normalizados guardados (interpolación lineal entre V vecinos,
≤1,0 s, mismo segmento; reproduce exp2 §5.3 exactamente). Cada detección verificada con
crop 480×480 a resolución original + cruz roja, uno a uno. **De 11 candidatos, 10 son FP
confirmados y 1 es el balón real.**

| Clip | Detector | t | Posición (conf) | Objeto real | Veredicto |
|---|---|---|---|---|---|
| B3 | YOLO | 79,6 | (1787,231) @0,273 | Valla publicitaria (borde rojo/blanco del panel F50) | **FP** |
| B3 | YOLO | 96,4 | (1649,294) @0,386 | Pecho/camiseta de BUL 15 | **FP** |
| B3 | YOLO | 100,2 | (1645,698) @0,375 | Media verde del portero (BUL 21) en el suelo | **FP** |
| B3 | YOLO | 100,2 | (1656,698) @0,265 | Media del portero — **mismo objeto** que la anterior (11 px, caja casi duplicada) | **FP** |
| B3 | cand1 | 79,6 | (939,510) @0,55 | **BALÓN REAL** (único caso a conf 0,40) — la interpolación falló en un chute en el scrum | **TP, no FP** |
| B3 | cand1 | 84,2 | (712,475) @0,378 | Hierba vacía (balón en la red) | **FP** |
| B3 | cand1 | 84,4 | (748,443) @0,348 | Hierba vacía junto a la línea de gol | **FP** |
| B3 | cand1 | 84,4 | (212,530) @0,272 | Bota/media de ESP 8 (pie rojo junto a la línea de gol) | **FP** |
| B3 | cand1 | 84,6 | (174,522) @0,27 | Bota/media de ESP 8 | **FP** |
| B3 | cand1 | 84,6 | (164,522) @0,305 | Bota/media de ESP 8 — **mismo objeto** que la anterior (10 px, caja casi duplicada) | **FP** |
| B1 | YOLO | 169,6 | (126,665) @0,307 | Hierba vacía junto a la línea de gol (guante/bota a ~60 px, no en la cruz) | **FP** |

Consecuencia: el caso cand1 B3 79,6 — contado como «lejos de la trayectoria» en exp2 §5.3 —
no era un error del detector sino un fallo de la interpolación. En conf 0,25, los «lejos»
de B3 cand1 pasan de 6 a 5 FP reales.

## 2. Evaluador corregido y métricas antes/después

**Script nuevo:** `scripts/exp3-evaluate.py` (no se tocó `scripts/exp2-evaluate.py`; cambio
documentado en su cabecera). `precision_adjudicable = tp / (tp + fp_V + fp_A)`; detecciones
en fotogramas NL aparte como `unknown_dets_NL` (con su conteo de fotogramas); `precision_legacy_exp2`
conservada para el antes/después; `--subset` / `--subset-ext` para el subconjunto B3;
`--legacy` reproduce los valores publicados de exp2. Salidas:
`docs/decisions/exp3/eval-corrected-b1.json`, `eval-corrected-b3.json`.

**Tolerancia 50 px — antes (exp2, precisión legacy) → después (v3):**

### B1 (145 V / 6 NL / 0 A)

| Detector | conf | Rec. antes → después | Prec. legacy antes → después | Prec. adjudicable (nueva) | Desconocidas NL |
|---|---|---|---|---|---|
| YOLO | 0,05 | 0,580 → 0,586 | 0,117 → 0,120 | 0,158 | 5 dets / 2 fot. |
| YOLO | 0,10 | 0,566 → 0,572 | 0,179 → 0,183 | 0,279 | 5 / 2 |
| YOLO | 0,25 | 0,455 → **0,462 (67/145)** | 0,281 → 0,290 | **0,554** | 0 |
| YOLO | 0,40 | 0,371 → 0,366 | 0,381 → 0,381 | 0,697 | 0 |
| YOLO | 0,60 | 0,203 → 0,200 | 0,630 → 0,630 | 0,829 | 0 |
| cand1 | 0,05 | 0,797 → 0,800 | 0,161 → 0,163 | 0,309 | 11 / 5 |
| cand1 | 0,10 | 0,783 → 0,793 | 0,234 → 0,240 | 0,439 | 6 / 4 |
| cand1 | 0,25 | 0,748 → **0,759 (110/145)** | 0,296 → 0,305 | **0,582** | 3 / 3 |
| cand1 | 0,40 | 0,678 → 0,690 | 0,319 → 0,329 | 0,645 | 1 / 1 |
| cand1 | 0,60 | 0,413 → 0,407 | 0,415 → 0,415 | 0,819 | 0 |

### B3 (76 V / 57 NL / 5 A)

| Detector | conf | Rec. antes → después | Prec. legacy antes → después | Prec. adjudicable (nueva) | Desconocidas NL |
|---|---|---|---|---|---|
| YOLO | 0,05 | 0,797 → 0,789 | 0,144 → 0,147 | 0,270 | 81 dets / 33 fot. |
| YOLO | 0,10 | 0,797 → 0,789 | 0,225 → 0,229 | 0,435 | 27 / 17 |
| YOLO | 0,25 | 0,716 → **0,711 (54/76)** | 0,356 → 0,362 | **0,771** | 4 / 3 |
| YOLO | 0,40 | 0,595 → 0,592 | 0,404 → 0,413 | 0,849 | 2 / 2 |
| YOLO | 0,60 | 0,392 → 0,395 | 0,382 → 0,395 | 0,909 | 2 / 2 |
| cand1 | 0,05 | 0,892 → 0,895 | 0,140 → 0,144 | 0,489 | 137 / 44 |
| cand1 | 0,10 | 0,878 → 0,882 | 0,211 → 0,218 | 0,626 | 71 / 35 |
| cand1 | 0,25 | 0,878 → **0,882 (67/76)** | 0,269 → 0,277 | **0,713** | 29 / 19 |
| cand1 | 0,40 | 0,851 → 0,855 | 0,310 → 0,320 | 0,783 | 8 / 7 |
| cand1 | 0,60 | 0,568 → 0,566 | 0,372 → 0,381 | 0,915 | 1 / 1 |

**Lectura.** Los cambios de recuperación son pequeños y están totalmente explicados por las
correcciones de referencia (B1: +169,4 TP para ambos detectores, +169,8 TP tras la corrección
de posición, +169,6 TP solo para cand1; B3: +96,4 TP en conf 0,25 vía YOLO (1168,872)@0,855,
+79,6/+96,4 para cand1). La precisión adjudicable es sistemáticamente mayor que la legacy
porque la legacy contaba como FP detecciones en fotogramas O que ahora son NL (desconocidas)
o V. El salto grande en B3 cand1 conf 0,05 (137 desconocidas / 44 fotogramas) muestra que
a baja confianza el detector dispara mucho sobre fotogramas no localizables — ese es el
coste real que la métrica legacy ocultaba. Comprobación de coherencia: los conteos de
detecciones en O cuadran (p. ej. B3 cand1 conf 0,05: 154 dets en O en exp2 → 144 =
137 desconocidas + 7 fp_A, tras mover 10 dets a los nuevos fotogramas V).

**Subconjunto B3 (recuperación, tol 50):** n=20 — YOLO 0,100 (2/20) @0,25, cand1 **0,550
(11/20)** @0,25 (idéntico a lo publicado en exp2); n=22 — YOLO 0,136 (3/22), cand1 0,591
(13/22) @0,25. El error de localización mediano de YOLO en B3 sigue en 0,4 px (la referencia
deriva de YOLO por construcción; no interpretable).

## 3. Ejemplos negativos verificados

`docs/decisions/exp3/negatives.csv` — 22 ejemplos, todos verificados uno a uno con crop
480×480 2× con cruz en la detección (columnas: clip, t_abs, category, object, x, y,
detector, conf, how_verified, source). Confianzas tomadas de los JSON normalizados.

| Categoría | n | Ejemplos |
|---|---|---|
| Botas/medias | 5 | B3 cand1 84,4 (212,530)@0,272 y 84,6 (174,522)@0,27 (pie rojo 8); B3 YOLO 99,6 (1450,691)@0,792, 100,2 (1645,698)@0,375 (media del portero); B3 YOLO 14,4 (1177,579)@0,107 (pierna/bota del portero) |
| Postes | **0** | **Sin ejemplos verificables centrados en el poste.** Las cajas del track 3 de 1C (B1 S4) están en la *zona* poste/red pero centradas en hierba + una mota blanca junto a la red (ver «Red»). Se declara explícitamente en vez de inventarlos. |
| Red | 3 | B1 YOLO 200,4 (1435,666)@0,271; 200,6 (1450,669)@0,386; 201,4 (1500,676)@0,328 — hierba junto a la esquina exterior inferior de la red, con mota blanca; balón real a 100–350 px (manos del portero / línea de gol). Track 3 de 1C (199,2–201,8). |
| Publicidad/vallas | 4 | B3 YOLO 55,0 (1472,327)@0,074 (panel Halcón); 56,2 (1354,293)@0,224 (mayordomo tras la valla); 78,4 (1336,220)@0,158 (valla oscura); 79,6 (1787,231)@0,273 (valla F50) |
| Tambor de grada | 3 | B3 YOLO 57,2 (516,246)@0,064; 57,8 (515,200)@0,091 (mismo tambor); 83,6 (440,260)@0,142 (otro tambor) |
| Logos | 3 | B3 YOLO 54,4 (906,429)@0,074; 55,4 (1748,320)@0,058; 55,8 (742,427)@0,116 — checkmark blanco del logo Halcón en la valla LED |
| Hierba vacía | 3 | B3 cand1 84,2 (712,475)@0,378; 84,4 (748,443)@0,348; B1 YOLO 169,6 (126,665)@0,307 |
| Pecho/camiseta | 1 | B3 YOLO 96,4 (1649,294)@0,386 (pecho de BUL 15) |

## 4. Muestra de comprobación ciega

Ver `docs/decisions/exp3/check-sample-b3.csv` + `check-sample-method.md` (método completo).

- **Ventanas por tiempo, sin consultar predicciones** (sondeo a 1 fps, fuera de C1–C4):
  D1 20,0–23,8 · D2 89,0–92,8 · D3 102,0–105,8 (60 fotogramas a 5 fps). Sin cortes
  (D1 verificado por diferencia entre fotogramas a 25 fps, MAD 2,0–5,5 sin picos; el cambio
  de encuadre 22,2→22,4 es un zoom-out, no un corte). Ninguna ventana sustituida.
- **Anotación ciega** (hojas sin cajas) + **verificación fotograma a fotograma con zoom 3×**.
- **Composición final: 48 V / 12 NL / 0 A** (D1 14/6, D2 15/5, D3 19/1).
- **Hallazgo metodológico:** el grounding a ciegas NO es fiable sin verificación — solo 3 de
  60 puntos estaban exactos; el resto tenía un desplazamiento sistemático de ~15–110 px
  (casi siempre arriba-izquierda del balón) y en 4 fotogramas de D1 apuntaba a objetos que
  no eran el balón (carteles VALLADOLID/MAPFRE/adidas). La verificación corrigió 45 posiciones
  y convirtió 12 fotogramas en NL. Misma lección que en 1C: ninguna posición por grounding se
  publica sin verificación por zoom.

## 5. Hipótesis de cajas duplicadas — veredicto: SE SOSTIENE

`docs/decisions/exp3/duplicates-analysis.json`. Método: casi-duplicado = ≥2 dets cand1
(conf≥0,05) a ≤50 px del balón real en el mismo fotograma V; cambios de id replicados
exactamente según `exp2-evaluate-linker.py` sobre la referencia v2 (B1 28, B3 14 — coinciden
con `linker-eval-cand1-*.json` guardados).

- Cand1 pone ≥2 cajas SOBRE el balón en el 72 % (103/143) de los fotogramas V de B1 y el
  84 % (62/74) de B3; media 2,85 / 3,36 cajas sobre el balón por fotograma V (YOLO: 1,36 /
  2,04); ≥2 cajas fuertes (≥0,25) sobre el balón: 82/143 B1, 60/74 B3.
- En los cambios de id, el id viejo y el nuevo se observan SIMULTÁNEAMENTE sobre el balón:
  mismo fotograma 15/28 B1 + 6/14 B3 (21/42); ventana ±0,2 s: 26/28 + 10/14 (36/42).
  Los cambios oscilan entre los mismos pares de ids (3↔4, 4↔6, 1↔2, 6↔9).
- Fotogramas V con ≥2 ids distintos simultáneamente sobre el balón: cand1 30/143 B1 (21 %),
  16/74 B3 (22 %); control (enlazador YOLO): 1/143 B1, 0/74 B3, con 2 y 0 cambios de id.
- **Veredicto: la hipótesis se sostiene** — el enlazador mantiene dos tracks paralelos sobre
  el mismo balón alimentados por cajas duplicadas y alterna entre ellos.
- **Caveats:** la coincidencia bruta ±0,2 s por sí sola no informa (los duplicados son casi
  ubicuos: 135/143 fotogramas V de B1 tienen ≥1 par ≤30 px); la evidencia fuerte es el
  track paralelo en el mismo fotograma + el contraste con el control YOLO. 6/42 cambios no
  tienen tracks paralelos en ventana (otras causas, p. ej. oclusión + re-adquisición como id
  nuevo). Un paso de deduplicación antes del enlazador es una *propuesta para decisión del
  usuario*, NO se implementa (fuera de alcance: sin rediseño del seguimiento).

## Archivos producidos

| Archivo | Contenido |
|---|---|
| `scripts/exp3-evaluate.py` | Evaluador corregido (nuevo; exp2 intacto) |
| `docs/decisions/exp3/ref-positions-b1-v3.csv` | Referencia B1 v3 (145 V / 6 NL / 0 A) |
| `docs/decisions/exp3/ref-positions-b3-v3.csv` | Referencia B3 v3 (76 V / 57 NL / 5 A) |
| `docs/decisions/exp3/eval-corrected-b1.json` | Métricas corregidas B1 (tol 25/50/100) |
| `docs/decisions/exp3/eval-corrected-b3.json` | Métricas corregidas B3 + subconjuntos 20/22 |
| `docs/decisions/exp3/negatives.csv` | 22 negativos verificados (postes: 0, declarado) |
| `docs/decisions/exp3/check-sample-b3.csv` | Muestra ciega B3 (60 fot.: 48 V / 12 NL) |
| `docs/decisions/exp3/check-sample-method.md` | Método de la muestra + hallazgo del grounding |
| `docs/decisions/exp3/duplicates-analysis.json` | Análisis de duplicados + veredicto |
| `docs/decisions/exp3/exp3-evaluacion-corregida-2026-11-07.md` | Este informe |

## Salvedades y pendientes para el padre

1. **Corrección incidental B1 169,8** (V→V, (1048,608)→(966,609)): fuera del alcance
   estricto de 1a; aceptar o revertir antes de commitear.
2. **Las métricas del enlazador siguen sobre la referencia v2** (la corrección de 169,8 no
   se propagó a las métricas del linker; fuera de alcance).
3. **La precisión de B3 YOLO (loc-err mediana 0,4 px) no es interpretable**: la referencia
   B3 deriva de YOLO por construcción.
4. En `docs/decisions/exp3/` ya existían archivos de otra línea de trabajo
   (`conditions-verification.md`, `data.yaml`, `finetune-recipe.md`) y
   `scripts/exp3-prepare-h250.py`: **no se tocaron**.
5. No se hizo commit ni push, como se ordenó.
