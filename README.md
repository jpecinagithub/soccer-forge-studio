# Soccer Forge Studio

Análisis de vídeo de fútbol con agente **Muse Spark 1.3** (`muse-spark-1.3`) + herramientas especializadas de visión + dashboard conectado a evidencias del vídeo.

> Estado: **Fase 0 cerrada (2026-11-06)**. Este repo documenta el producto y su despliegue. No hay todavía implementación del pipeline ni despliegue en producción. Nada de lo documentado aquí debe leerse como verificado en vivo hasta que la Fase 1 lo mida. Los cuatro entregables de Fase 0 están en `docs/`: definiciones exactas de eventos, contrato de datos, set de evaluación y criterios de aceptación.

## Flujo del usuario

Subir vídeo → comprobar archivo → analizar en segundo plano → abrir dashboard → revisar jugadas y corregir resultados → exportar. Se puede cerrar y volver más tarde; el resultado puede ser completo o parcial, con sus limitaciones explicadas.

## Qué es una jugada

- **Evento:** pase, recuperación, conducción, duelo, tiro, pérdida.
- **Jugada:** secuencia de eventos relacionados, desde una recuperación o reinicio hasta un desenlace, interrupción o pérdida.
- Cada jugada lleva tiempo (del archivo, separado del reloj del partido), participantes, acciones, localización, interpretación, calidad/incertidumbre, evidencia (fragmento exacto) y revisión/historial.

V1 prioriza pases, conducciones, recuperaciones, pérdidas y tiros.

## Reglas duras

- Un ID de seguimiento **no** es automáticamente un dorsal o un nombre.
- Jugador fuera de cámara = posición desconocida hasta recuperarlo con evidencia.
- En primeros planos o repeticiones se suspenden las métricas que dependan de una vista válida del campo.
- Distancias y velocidades solo sobre tramos calibrados y trayectorias estables.
- Ninguna conclusión sin referencia temporal a su evidencia.

## Monorepo

```
apps/web       # Vite + React + TS — dashboard (vídeo, campo 2D, jugadas, timeline, inspector)
apps/api       # Node 20 + TS — REST, subida, biblioteca, correcciones, exportación
apps/worker    # Node 20 + TS — pipeline: ffmpeg, visión, seguimiento, eventos, Muse Spark
packages/shared # Tipos y contratos entre api, worker y web
infra/deploy   # docker-compose.yml + nginx — despliegue en Oracle
docs/          # Especificación, despliegue, arquitectura, diccionario de eventos
```

Todo el despliegue vive en el servidor Oracle (sin Vercel para este proyecto, por decisión del usuario el 2026-11-06: el vídeo largo y la cola de trabajos necesitan el servidor). Ver [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Documentación

- [SPEC.md](SPEC.md) — especificación inicial completa (resumen de la propuesta del 2026-11-06).
- [docs/EVENT_DICTIONARY.md](docs/EVENT_DICTIONARY.md) — definiciones exactas de los eventos v1 (Fase 0).
- [docs/DATA_CONTRACT.md](docs/DATA_CONTRACT.md) — contrato de datos de cada jugada y su evidencia (Fase 0).
- [docs/EVALUATION_SET.md](docs/EVALUATION_SET.md) — clips de evaluación con anotaciones humanas (Fase 0; clips pendientes de aportar).
- [docs/ACCEPTANCE_CRITERIA.md](docs/ACCEPTANCE_CRITERIA.md) — criterios medibles Go / No-Go de la Fase 1 (Fase 0).
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — despliegue monorepo en Oracle, paso a paso.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — arquitectura, pipeline y contratos de datos.

## Fases

0. Especificación · 1. Viabilidad (clips reales, Muse directo vs sistema combinado) · 2. Ingesta · 3. Seguimiento · 4. Jugadas · 5. Dashboard · 6. Agente táctico · 7. Partidos completos · 8. Piloto.

Primero clips cortos, luego 10 minutos, luego partidos completos. Sin fecha cerrada hasta medir la Fase 1.

## Autor

Jon Peciña ([jpecina](https://github.com/jpecinagithub)).
