# Diccionario de eventos — v1 (Fase 0)

> Borrador inicial. Cada evento necesita, antes de implementarse: definición, ejemplos, casos límite y prueba. Los umbrales numéricos se fijan en la Fase 1, no aquí.

## Eventos v1 (prioritarios)

| Evento | Definición provisional | Resultado |
|---|---|---|
| `pass` | Un jugador envía el balón a un compañero y el balón cambia de poseedor | completado / interceptado / fuera |
| `carry` | Un jugador desplaza el balón bajo control durante una distancia apreciable | en curso / termina en pase, tiro o pérdida |
| `recovery` | Un equipo recupera la posesión sin que el rival la pierda por error propio claro | — |
| `loss` | Pérdida de la posesión (pase fallido, robo, fuera) | — |
| `shot` | Intento de marcar, con el balón dirigido a portería | gol / parado / fuera / bloqueado |

## Eventos posteriores (con definiciones y pruebas propias)

Duelos, presión, desmarques y ruptura de líneas. No se implementan hasta tener su definición y su prueba.

## Reglas de anotación

- Una repetición televisiva no genera eventos nuevos.
- En primeros planos o repeticiones no se anotan métricas que dependan de una vista válida del campo.
- Distancias y velocidades solo sobre tramos calibrados y trayectorias suficientemente estables.
- Jugador desconocido se marca como desconocido; nunca se inventa una identidad.
- Todo evento lleva `tStart` y `tEnd` en tiempo de archivo, confianza y enlace a su evidencia.
