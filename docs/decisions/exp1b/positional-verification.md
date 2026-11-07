# Verificación posicional de las detecciones de balón (P640 y P1280) — Experimento 1B

Método: hojas anotadas `data/clips/work/exp1b/annotated/sheet-01..17.jpg`
(cajas dibujadas sobre los fotogramas etiquetados, 1920×1080).
Cada caja se juzga visualmente: TP si cae sobre el balón real,
FP si cae en otro lugar, ? si no se puede resolver a 960 px.
Las etiquetas V/?/N son revisión visual directa (labels.csv).
Registro por caja: `docs/decisions/exp1b/box-verdicts.csv`
(159 cajas); cálculo mecánico: `scripts/exp1b-verified.py`.
El cruce con los JSON es total (0 cajas sin correspondencia):
cada conf registrada existe en el JSON de su variante y fotograma
(±0,015). Dos cajas se corrigieron tras el cruce por su bbox:
170.4 P1280 0.07 → 0.17, 75.2 P1280 0.60 → 0.599 (valor real).
Dos cajas P1280 solapadas en 164.6 (0.26, 0.22) y dos en 171.2
(0.46, 0.18) no se veían en las hojas (etiquetas tapadas); se
juzgaron por su bbox frente a la caja TP del mismo fotograma: las 4 FP.

## P640 (36 cajas)

- 23 TP, 13 FP, 0 ? → precisión por caja 23/36 = **63,9 %**.
- Precisión por banda: conf ≥0.40: 5/5 (100 %); 0.25–0.40: 0/1 (0 %);
  0.10–0.25: 7/10 (70 %); 0.05–0.10: 11/20 (55 %).
- La caja P640 de 75.2 (0.05) se resolvió como TP gracias a la caja
  P1280 0.599 en el mismo punto.
- Fotogramas V con SOLO cajas FP: 76.8, 137.6, 138.4, 195.2.

Recuperación VERIFICADA P640 (fotogramas V con ≥1 caja TP, de 77 V):
- 0.05 → 23/77 = **29,9 %** (nominal 35,1 %)
- 0.10 → 12/77 = 15,6 % (nominal 18,2 %)
- 0.25 → 5/77 = 6,5 % (nominal 6,5 %)
- 0.40 → 5/77 = 6,5 % (nominal 6,5 %)
- 0.60 → 1/77 = 1,3 % (nominal 1,3 %)

## P1280 (123 cajas)

- 56 TP, 65 FP, 2 ? → precisión por caja 56/121 = **46,3 %**.
- Precisión por banda: conf ≥0.40: 25/28 (89,3 %); 0.25–0.40: 15/19
  (78,9 %); 0.10–0.25: 12/42 (28,6 %); 0.05–0.10: 4/31 (12,9 %).
- Las cajas de conf ≥0.25 son mayoritariamente TP (40/47 = 85,1 %);
  por debajo de 0.10 casi todo es FP (4/31 = 12,9 %).
- Fotogramas V con SOLO cajas FP: 70.4, 76.8, 137.6, 138.4, 195.6, 201.2.
- Fotogramas V sin ninguna detección P1280: 20 (134.4, 168.8 y 195.2
  tienen solo caja P640; 17 no tienen detección en ninguna variante).

Recuperación VERIFICADA P1280 (fotogramas V con ≥1 caja TP, de 77 V):
- 0.05 → 51/77 = **66,2 %** (nominal 74,0 %)
- 0.10 → 48/77 = 62,3 % (nominal 72,7 %)
- 0.25 → 37/77 = 48,1 % (nominal 49,4 %)
- 0.40 → 25/77 = 32,5 % (nominal 33,8 %)
- 0.60 → 6/77 = 7,8 % (nominal 7,8 %)

## Fotogramas ? y N

- 70.8 (?), 135.2 (?), 141.2 (?), 170.8 (?): sin detecciones P640;
  P1280 tiene 1 caja FP en 70.8 (0.18) y 1 caja ? en 135.2 (0.12);
  141.2 y 170.8 sin detecciones en ninguna variante.
- 171.6 (N, primer plano del portero): P640 2 FP (0.37, 0.09);
  P1280 2 FP (0.28 y una segunda caja cian <0.25 sobre el césped).
  El umbral 0.25 NO elimina los falsos positivos en primeros planos.

## Conclusión de esta verificación

La recuperación nominal sobreestima la real en ambas resoluciones,
más a 640 (35,1 % → 29,9 %) que a 1280 (74,0 % → 66,2 %).
A 1280 la señal es real: a conf ≥0.25 la precisión es del 85 % y la
recuperación verificada del 48,1 %; a conf 0.05 la recuperación sube
al 66,2 % pero la precisión por caja cae al 46 % (muchos FP de
confianza baja). El punto de trabajo razonable está en torno a 0.25.
