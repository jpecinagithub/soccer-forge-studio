# Soccer Forge Studio — Especificación inicial (2026-11-06)

Fuente: propuesta completa del usuario en el side chat del 2026-11-06 (11 secciones). Este archivo es el resumen fiel; el texto íntegro queda en ese chat.

## Producto
Análisis de vídeo de fútbol con agente Muse Spark 1.3 (`muse-spark-1.3`) + herramientas especializadas de visión + dashboard conectado a evidencias del vídeo.

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
- **Muse Spark 1.3 dentro del producto:** coordinar herramientas, revisar secuencias ambiguas, generar explicaciones tácticas.
- Las herramientas especializadas aportan detecciones, trayectorias y mediciones. Comparar Muse directo vs sistema combinado en Fase 1.

Pendiente de comprobar antes de integrar: acceso real de la cuenta, límites de vídeo, costes y comportamiento de la API.

## Pipeline interno (etapas verificables)
Recepción → Preparación → Segmentación (planos, cortes, repeticiones) → Percepción → Seguimiento → Calibración → Eventos → Revisión con Muse → Validación → Publicación. Cada etapa guarda su resultado; un fallo recuperable no obliga a repetir todo.

## Reglas fijadas desde el principio
- ID de seguimiento ≠ dorsal o nombre automáticamente.
- Jugador fuera de cámara = posición desconocida hasta recuperarlo con evidencia.
- Asociaciones dudosas corregibles.
- En primeros planos o repeticiones se suspenden métricas que dependan de vista válida del campo.
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

## Despliegue (2026-11-06)
Monorepo, todo en el servidor Oracle (decisión del usuario; sin Vercel para este proyecto). Repo: https://github.com/jpecinagithub/soccer-forge-studio. Detalle completo, paso a paso, en [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): servidor `iadelveloper-server` (143.47.63.169, Node 20.20.2, Docker 29.5.0, ffmpeg 6.1.1, 122 G libres, sin GPU detectada), URL propuesta `https://jpecina.duckdns.org/soccer/`, puertos web 4310 / api 4300 (solo localhost, vía nginx), Postgres 16 + Redis 7 internos, volúmenes `soccer_pgdata` / `soccer_redisdata` / `soccer_media`, `restart: unless-stopped` en todos los servicios. Despliegue documentado, NO ejecutado todavía.
