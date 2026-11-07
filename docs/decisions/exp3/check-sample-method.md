# Muestra de comprobación ciega B3 — nota de método (exp3, 2026-11-07)

## Definición

- **Partido:** B3 (España 4–0 Bulgaria, `data/clips/espana-bulgaria-rfef.mp4`, 146,72 s). B1 es
  ajuste y B2 está reservado, así que la comprobación del futuro detector afinado se hace en B3.
- **Ventanas (elegidas POR TIEMPO, sin consultar predicciones):** tres ventanas de 3,8 s a 5 fps
  (20 fotogramas cada una, 60 en total), elegidas de un sondeo a 1 fps del partido completo,
  todas fuera de los segmentos C1–C4 de la referencia exp2:
  - **D1 20,0–23,8 s** — ataque de España por la izquierda, remate y rechace.
  - **D2 89,0–92,8 s** — ataque de España por la derecha, regate de Ferran Torres (7) y pase atrás.
  - **D3 102,0–105,8 s** — ataque de España en el descuento (90:00 +3), balón suelto en el área.
- **Cortes:** D1 verificado sin cortes (diferencia media entre fotogramas consecutivos a 25 fps,
  21,8–23,2 s: MAD 2,0–5,5, sin picos; el cambio de encuadre entre 22,2 y 22,4 es un zoom-out
  rápido de cámara, no un corte). D2 y D3: reloj continuo, cámara continua, trayectorias
  coherentes; sin cortes detectados. Ninguna ventana tuvo que sustituirse.

## Anotación (ciega, como en 1C)

1. Hojas de contacto sin cajas: 6 fotogramas por hoja (celdas 960×540), generadas con ffmpeg
   (`/tmp/exp3/check-sheet-00.png` … `-09.png`; `scripts/exp3-checksheets.py` en /tmp).
2. Posición inicial por fotograma con la herramienta de grounding sobre cada hoja, convertida
   celda → resolución original 1920×1080 (×2).
3. **Verificación fotograma a fotograma con zoom 3× (240×240) centrado en el punto de
   grounding** (y crops de 480×480 a 2× donde el punto caía fuera del balón o no había balón
   visible). Cada posición final está confirmada en zoom o corregida por lo que el zoom muestra;
   cada fotograma sin balón localizable se marca NL con su motivo.
4. Incertidumbre explícita: unc 20 (balón claro a pie de jugador), 25 (vuelo, parcialmente
   ocluido, o corrección >50 px), 30 (motion blur).
5. Columnas: `t_abs, segment, status, o_class, x, y, unc, source, note, v3_change`.
   `status` V = visible, NL = no localizable (balón en el fotograma pero posición no
   determinable de forma fiable: ocluido, en manos del portero, en vuelo con motion blur
   extremo). No hay ningún fotograma A (ausente confirmado) en la muestra.

## Hallazgo metodológico: el grounding a ciegas NO es fiable sin verificación

De los 60 fotogramas, solo **3 puntos de grounding estaban exactos** (20,0; 102,4; 105,0).
El resto tenía un desplazamiento sistemático de **~15–110 px** (casi siempre hacia arriba
y a la izquierda del balón real, coherente con un error de conversión hoja→original), y en
**4 fotogramas de D1 el grounding apuntaba a objetos que no eran el balón** (carteles
VALLADOLID/MAPFRE/adidas en 22,0, 22,2, 23,0 y 23,2). La verificación por zoom corrigió
45 posiciones y convirtió 12 fotogramas en NL. **Lección para el futuro (misma que en 1C):
ninguna posición anotada por grounding se publica sin verificación por zoom.**

## Composición final

| Ventana | V | NL | A | Contenido |
|---|---|---|---|---|
| D1 20,0–23,8 | 14 | 6 | 0 | Duelo y control de pecho (21,2 NL), scrum (22,4–22,6 NL), parada del portero (23,2 V; 23,4–23,8 NL) |
| D2 89,0–92,8 | 15 | 5 | 0 | Regate de Ferran Torres (7), pase (90,0 NL), chute (91,0–91,2 NL), recepción de ESP 8 (91,8–92,0 NL) |
| D3 102,0–105,8 | 19 | 1 | 0 | Conducción y balón suelto en el área; solo 102,6 NL (ocluido tras ESP 16) |
| **Total** | **48** | **12** | **0** | **60 fotogramas** |

## Uso previsto

- Evaluar el detector afinado (fine-tuning, exp3 parte B/C) con el mismo evaluador
  (`scripts/exp3-evaluate.py`): recuperación sobre los 48 V, detecciones en los 12 NL como
  desconocidos (aparte, no como FP), tolerancia 50 px.
- La muestra NO es una muestra sin sesgo del partido: son tres ventanas de juego abierto
  elegidas por tiempo. No extrapolar sus métricas a todo el partido.
- Cualquier corrección futura a esta muestra debe hacerse por el mismo procedimiento
  (zoom 3× por fotograma) y registrarse en `v3_change`.
