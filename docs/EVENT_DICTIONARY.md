# Diccionario de eventos — v1 (Fase 0, cerrado 2026-11-06)

> **Carácter normativo.** Estas definiciones son la fuente que debe seguir la implementación. Ante un caso que no encaje, el sistema lo marca `pending` y no inventa una clasificación. Ningún umbral de este documento se cambia durante la Fase 1 sin anotarlo como cambio de criterio, con fecha y motivo.
>
> Tiempos en **segundos del archivo** con dos decimales. El reloj del partido es otro campo y nunca sustituye al tiempo de archivo.

## 0. Bases comunes

- **Desconocido es un valor, no un hueco.** Jugador no identificado: `playerId: null` + `unknown: true`. Nunca se asigna un dorsal o un nombre por parecido, por posición o por contexto.
- **Confianza 0..1.** `confidence < 0.60` → el evento o la jugada quedan en estado `pending` y exigen revisión humana. La confianza no se redondea al alza para pasar el corte.
- **Caso ambiguo → `pending`.** Si dos interpretaciones son razonables con la evidencia disponible, se publica la duda, no la más probable.
- **Una repetición no es otra jugada.** Ver §1.

## 1. Segmentos: qué se puede medir en cada tramo

Cada segundo del archivo pertenece a un tipo de segmento, decidido en la etapa de segmentación:

| Segmento | Descripción | Métricas con geometría | Conteo de eventos y tiempos |
|---|---|---|---|
| `field-view` | Vista amplia del campo, calibración válida | Permitidas | Permitidos |
| `close-up` | Primer plano (jugador, banquillo, grada) | **Suspendidas** | No se anotan eventos nuevos |
| `replay` | Repetición de una acción ya emitida en directo | **Suspendidas** | No se anotan eventos nuevos |
| `excluded` | Interrupción, fuera de cobertura, imagen no utilizable | Suspendidas | No se anotan eventos nuevos |

- **Métricas que requieren geometría válida del campo** (y por tanto se suspenden en `close-up`, `replay` y `excluded`): posiciones, trayectorias, distancias, velocidades, zonas, mapas de calor y cualquier derivado (por ejemplo, ruptura de líneas).
- **Una repetición puede ayudar a revisar una acción, pero no contabilizarse como otra jugada.** Si la repetición permite confirmar o corregir un evento ya detectado en el tramo en directo, la corrección se anota sobre el evento original, con sus tiempos de archivo en directo. La repetición nunca genera eventos, jugadas ni estadísticas nuevas.
- **Un primer plano no borra lo anterior.** La trayectoria de un jugador que entra en primer plano queda en estado desconocido hasta que reaparece en una vista válida con evidencia suficiente para reidentificarlo.
- El dashboard debe mostrar, para cada jugada, en qué tipo de segmento se apoya su evidencia.

## 2. Jugada

Una **jugada** es una secuencia de eventos relacionados con posesión de un mismo equipo.

- **Inicio:** recuperación del balón, o reinicio (saque inicial, saque de banda, falta, córner, saque de puerta, saque de centro tras gol).
- **Fin:** gol, tiro, pérdida de posesión, falta, balón fuera, final del tramo analizable, o interrupción del juego.
- **Corte entre jugadas:** el cambio de posesión cierra la jugada anterior y abre la siguiente. Un balón dividido sin control claro no abre jugada nueva: queda como cola de la anterior hasta que haya control o interrupción.
- **Contenido mínimo:** al menos un evento, `tStart`, `tEnd`, equipo, estado de revisión y evidencia. Una jugada sin evidencia enlazada no se publica.
- **Tolerancia de evaluación:** el inicio y el fin de una jugada se consideran correctos si difieren ≤ 1,0 s de la anotación humana en cámara táctica y ≤ 2,0 s en retransmisión (ver `ACCEPTANCE_CRITERIA.md`).

## 3. `pass` — pase

- **Definición:** un jugador golpea o toca el balón con la intención de entregarlo a un compañero, y el balón cambia de zona o de poseedor.
- **Inicio (`tStart`):** último contacto del pasador con el balón.
- **Fin (`tEnd`):** primer contacto controlado del receptor, o intercepción, o salida del balón del campo.
- **Evidencia mínima:** pasador identificado (o desconocido explícito) y trayectoria del balón visible en al menos dos instantes entre inicio y fin.
- **Resultado:** `completed` (lo controla un compañero) · `intercepted` (lo corta un rival) · `out` (sale del campo sin receptor) · `blocked` (desvío rival inmediato que impide el pase).
- **Casos límite:**
  - Pase al espacio sin receptor inmediato: se anota si un compañero llega antes que el rival; si no llega nadie, `out` o `intercepted` según lo que ocurra, y la intención queda en `notes`, no en el resultado.
  - Desvío leve que no cambia el receptor: sigue siendo el mismo pase.
  - Balón que rebota en un rival y vuelve al mismo equipo: no es pase nuevo; es continuación.
- **No cuenta como pase:** un despeje sin destinatario, un tiro (ver §7), un control orientado sin entrega.

## 4. `carry` — conducción

- **Definición:** un jugador desplaza el balón bajo control, sin pasarlo ni tirar.
- **Inicio:** primer contacto controlado que inicia el desplazamiento.
- **Fin:** pase, tiro, pérdida, interrupción, o final del desplazamiento controlado.
- **Condición de registro:** desplazamiento ≥ 3 m **y** duración ≥ 1 s. Por debajo de ambos umbrales, el movimiento se registra como control, no como conducción.
- **Evidencia mínima:** trayectoria del jugador y del balón en vista válida del campo durante todo el tramo; en `close-up` o `replay` no se anota conducción nueva.
- **Resultado:** `ongoing` no es un resultado final: toda conducción publicada termina en `pass`, `shot`, `loss` o `stoppage`.
- **Caso límite:** conducción que cruza un corte de cámara sin cambio de plano: se mantiene si la reidentificación es segura; si no, se cierra la conducción y se abre una nueva solo cuando haya control confirmado.

## 5. `recovery` — recuperación

- **Definición:** un equipo vuelve a tener la posesión controlada tras haberla tenido el rival.
- **Inicio:** primer contacto controlado del jugador que recupera.
- **Fin:** el instante en que la posesión se considera establecida (control + siguiente acción o 1 s de control continuado).
- **Evidencia mínima:** contacto controlado visible y equipo recuperador identificado.
- **Casos límite:**
  - Intercepción de un pase: es a la vez resultado `intercepted` del pase rival y `recovery` propia.
  - Balón dividido que queda suelto: no hay recuperación hasta que haya control; la pérdida rival queda con `recovery: unknown`.
  - Recuperación tras despeje rival: sí cuenta, si hay control posterior.
- **No cuenta como recuperación:** tocar el balón sin controlarlo, ni un rechace que sigue en posesión rival.

## 6. `loss` — pérdida

- **Definición:** un equipo pierde la posesión controlada del balón.
- **Inicio:** último contacto controlado antes de perderla.
- **Fin:** el instante en que el rival controla, el balón sale, o se sanciona la interrupción.
- **Resultado:** `failed-pass` (pase fallido) · `tackled` (robo/entrada rival) · `out` (fuera) · `foul` (pérdida por infracción propia).
- **Regla de pareado:** toda pérdida, salvo balón fuera o interrupción, debe enlazar con la `recovery` del rival; si la recuperación no se observa, se registra `recovery: unknown`, sin inventarla.
- **No cuenta como pérdida:** un pase completado a un compañero (aunque sea hacia atrás), ni un tiro.

## 7. `shot` — tiro

- **Definición:** intento de marcar, con el balón impulsado hacia la portería.
- **Inicio:** último toque que impulsa el balón hacia la portería.
- **Fin:** gol, parada, balón fuera por línea de fondo, bloqueo, o control del portero/rival.
- **Evidencia mínima:** trayectoria del balón hacia la portería visible, o portería en cuadro en el tramo del tiro.
- **Resultado:** `goal` · `saved` · `out` · `blocked`.
- **Casos límite:**
  - Tiro que desvía un rival y entra: es tiro, resultado `goal`; el desvío queda en `notes`.
  - Centro chutado que acaba en gol: se anota como tiro solo si la trayectoria y la intención son de tiro; en duda, `pending` con nota, no tiro automático.
  - Disparo desde muy lejos con balón que no llega: es tiro si hay intención y dirección a portería; si es un pase largo, es pase.
- **No cuenta como tiro:** un pase hacia la zona de portería sin intención de marcar, ni un despeje.

## 8. Criterios de aceptación por evento (para la implementación)

Cada evento publicado debe cumplir todo esto; si no, queda `pending`:

1. `tStart` y `tEnd` en tiempo de archivo, con `tEnd >= tStart`.
2. Tipo, resultado y participantes (o desconocido explícito).
3. `confidence` entre 0 y 1.
4. Enlace a un clip de evidencia que cubra el evento completo.
5. Ningún evento con `tStart` dentro de un segmento `replay` o `close-up` sin enlace a su evento original en directo.
6. Ninguna métrica de distancia, velocidad o posición sobre tramos no calibrados.
