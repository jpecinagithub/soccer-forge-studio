# Soccer Forge Studio — Especificación inicial (2026-11-06)

> **Estado (2026-11-08): proyecto cerrado en su estado experimental.
> Ver `docs/decisions/cierre-2026-11-08.md`.**

Fuente: propuesta completa del usuario en el side chat del 2026-11-06 (11 secciones). Este archivo es el resumen fiel; el texto íntegro queda en ese chat.

## Producto
Análisis de vídeo de fútbol con el agente Muse de Meta (que funciona con Muse Spark 1.3) + herramientas especializadas de visión + dashboard conectado a evidencias del vídeo.

> **Decisiones 2026-11-07 (corrección del usuario):**
>
> | Elemento | Decisión |
> |---|---|
> | Agente que desarrolla el proyecto | Muse de Meta |
> | Motor que analizará los vídeos en la aplicación | Pendiente de seleccionar y validar |
> | Uso obligatorio de Muse Spark 1.3 por API | No es un requisito |
> | Anotaciones realizadas por Muse | Material exploratorio para desarrollar y evaluar |
>
> Que Muse desarrolle el proyecto no significa que Muse deba analizar los vídeos de los usuarios: esa decisión sigue abierta. El flujo del producto es: el usuario sube un vídeo y la aplicación ejecuta el análisis automáticamente, sin que tenga que entregárselo manualmente al agente Muse.

Flujo: subir vídeo → comprobar archivo → analizar en segundo plano → abrir dashboard → revisar jugadas y corregir resultados → exportar. Se puede cerrar y volver más tarde; resultado completo o parcial con limitaciones explicadas.

Formatos v1 propuestos: MP4, MOV, MKV, AVI, WebM (sujetos a matriz comprobada de códecs). Archivo corrupto / protegido / códec no soportado = mensaje claro, no conversión manual obligatoria.

## Distinción clave
- **Evento:** pase, recuperación, conducción, duelo, tiro, pérdida.
- **Jugada:** secuencia de eventos relacionados, desde recuperación/reinicio hasta desenlace, interrupción o pérdida.
- Cada jugada: tiempo (archivo, separado del reloj del partido), contexto, participantes, acciones, localización, interpretación, calidad/incertidumbre, evidencia (fragmento exacto), revisión/historial.
- V1 prioriza: pases, conducciones, recuperaciones, pérdidas, tiros. Duelos, presión, desmarques y ruptura de líneas, después.

## Papel de Muse
Dos usos separados:
- **Muse como herramienta de desarrollo:** construir siguiendo especificaciones, tareas y pruebas.
- **Muse dentro del producto:** no. Muse es el agente de desarrollo (construir, probar, depurar). El motor que analizará los vídeos dentro de la aplicación está pendiente de selección mediante pruebas; no se exige Muse Spark ni una API concreta.
- Las herramientas especializadas aportan detecciones, trayectorias y mediciones. Comparar soluciones de análisis integrables en Fase 1 (ver `docs/decisions/engine-candidates-2026-11-07.md`).

Pendiente de comprobar antes de integrar, en **dos bloques separados** (matización del usuario 2026-11-06):
- **Bloque A — prueba técnica automatizable:** ejecutar el recorrido real desde la aplicación: subir un clip, procesarlo con las herramientas candidatas, generar eventos estructurados y abrir su evidencia. (Replanteo 2026-11-07: ya no es el acceso a un modelo por API.)
- **Bloque B — viabilidad:** precisión, tiempo y coste sobre nuestros vídeos.
Tener acceso no demuestra que el análisis sea suficientemente bueno. Ver `docs/ACCEPTANCE_CRITERIA.md`.

## Pipeline interno (etapas verificables)
Recepción → Preparación → Segmentación (planos, cortes, repeticiones) → Percepción → Seguimiento → Calibración → Eventos → Revisión con Muse → Validación → Publicación. Cada etapa guarda su resultado; un fallo recuperable no obliga a repetir todo.

## Reglas fijadas desde el principio
- ID de seguimiento ≠ dorsal o nombre automáticamente.
- Jugador fuera de cámara = posición desconocida hasta recuperarlo con evidencia.
- Asociaciones dudosas corregibles.
- En primeros planos o repeticiones se suspenden las métricas que dependan de vista válida del campo. Matización (2026-11-06): se suspenden las métricas que requieren **geometría válida del campo**. Una repetición puede ayudar a revisar una acción, pero **no contabilizarse como otra jugada**; la corrección se anota sobre el evento original en directo.
- Distancias/velocidades solo sobre tramos calibrados y trayectorias estables.
- Distancia observada ≠ distancia total del partido.
- Heatmaps muestran también tiempo visible.
- Interpretación táctica ≠ acción observada.
- Corregir jugador/evento actualiza estadísticas dependientes.
- Ninguna conclusión sin referencia temporal a su evidencia.

## Dashboard (5 áreas + resumen)
Vídeo (reproducción, velocidad, avance preciso, capas) · Campo 2D sincronizado (con indicación de datos ausentes) · Jugadas (filtrable por equipo, jugador, acción, estado de revisión) · Línea temporal (eventos, secuencias, interrupciones, cobertura) · Inspector (detalle, explicación, evidencia, correcciones). Más vistas de resumen, jugadores, métricas y exportaciones. El chat llega después de tener datos fiables; debe devolver jugadas concretas con enlaces o indicar falta de evidencia.

## Referencia (NO validación)
Post + vídeo 2:29 revisado visualmente: IDs de jugadores/árbitro/balón, campo 2D sincronizado, eventos, timeline, selector, heatmaps, dibujo, métricas/chat/clips. Presencia de controles no acredita funcionamiento. Observado: marcadores sobre primer plano y pases con distancias casi nulas — investigar antes de fiar métricas. Rendimiento declarado por el autor (10 min en <30 min) no asumible.

## Plan por fases
0. Especificación · 1. Viabilidad (clips representativos, Muse directo vs combinado) · 2. Ingesta · 3. Seguimiento · 4. Jugadas · 5. Dashboard · 6. Agente táctico · 7. Partidos completos · 8. Piloto.
Primero clips cortos, luego 10 min, luego partidos completos. Sin fecha cerrada ni promesa de rendimiento antes de medir Fase 1.

## Evaluación
Set con cámara táctica, TV y amateur; oclusiones, movimiento de cámara, primeros planos, balón poco visible, cambios de luz. Parte anotada manualmente, partidos reservados para evaluación. Métricas: aciertos/omisiones por evento, error en inicio/fin, cambios de identidad, exactitud de posiciones, % tiempo analizable, calibración incertidumbre-error, tiempo/coste por minuto, minutos de corrección, recuperación tras fallo.

## Paquete de trabajo para MUSE (sec. 11)
Especificación, inventario de funciones, diccionario de eventos, contratos de datos, diseño de pantallas y estados, conjunto de evaluación y criterios, tareas pequeñas ordenadas por dependencia, registro de decisiones y resultados. Primera tarea de implementación: recorrido completo vídeo → eventos con evidencia → revisión en pantalla sobre un clip real.

## Estado
2026-11-06: especificación recibida y guardada. Sin código, sin repo, sin objetivo creado. Pendiente: elegir primer paso (Fase 0 o Fase 1).

**Fase 0 cerrada 2026-11-06** con cuatro entregables: (1) definiciones exactas de los eventos v1 — `docs/EVENT_DICTIONARY.md`; (2) contrato de datos de cada jugada y su evidencia — `docs/DATA_CONTRACT.md`; (3) clips de evaluación con anotaciones humanas — `docs/EVALUATION_SET.md` + `docs/evaluation/annotation-template.json` (especificación y plantillas; los clips reales están pendientes de aportar por el usuario); (4) criterios medibles para decidir si la prueba con Muse permite avanzar — `docs/ACCEPTANCE_CRITERIA.md` (umbrales propuestos en Fase 0, fijados antes de ajustar modelos). Siguiente paso: comparación Muse directo frente a Muse con herramientas de visión, antes de construir el dashboard completo. Sin implementación iniciada.

## Despliegue (2026-11-06)
Monorepo, todo en el servidor Oracle (decisión del usuario; sin Vercel para este proyecto). Repo: https://github.com/jpecinagithub/soccer-forge-studio. Detalle completo, paso a paso, en [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): servidor `iadelveloper-server` (143.47.63.169, Node 20.20.2, Docker 29.5.0, ffmpeg 6.1.1, 122 G libres, sin GPU detectada), URL propuesta `https://jpecina.duckdns.org/soccer/`, puertos web 4310 / api 4300 (solo localhost, vía nginx), Postgres 16 + Redis 7 internos, volúmenes `soccer_pgdata` / `soccer_redisdata` / `soccer_media`, `restart: unless-stopped` en todos los servicios. Despliegue documentado, NO ejecutado todavía. **Cautela GPU (2026-11-06):** «sin GPU detectada» es información documentada, todavía no verificada — la comprobación fue que `nvidia-smi` no existe en el host, lo que no prueba la ausencia de hardware. Condiciona dónde ejecutar la visión especializada y debe resolverse en la prueba de viabilidad.
