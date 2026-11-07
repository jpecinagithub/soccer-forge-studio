# Motores candidatos para el análisis de vídeo — propuesta (2026-11-07)

Decisión del usuario 2026-11-07: Muse de Meta es el agente de desarrollo; el motor que analizará los vídeos dentro de la aplicación está **pendiente de selección mediante pruebas**. No se exige Muse Spark ni una API concreta. El producto debe ejecutar el análisis automáticamente (vídeo subido → procesamiento → jugadas con evidencia → dashboard), sin entregar el vídeo manualmente al agente Muse.

## Pruebas acordadas (2026-11-07)

| Prueba | Configuración inicial | Qué queremos comprobar |
|---|---|---|
| 1. Visión local | YOLO + un único seguidor, inicialmente ByteTrack | Detección de jugadores y balón, continuidad del seguimiento y rendimiento en Oracle |
| 2. Análisis visual por API | Qwen2.5-VL-72B-Instruct mediante OpenRouter | Reconocimiento de acciones, tiempos, repeticiones y resultados estructurados |
| 3. Híbrido | Pendiente | Solo construirlo si las pruebas muestran capacidades complementarias |

## Candidatos

### 1. Pipeline CV local: YOLO + ByteTrack + reglas

Detección de jugadores y balón (Ultralytics YOLO), seguimiento con ByteTrack, calibración del campo por homografía y eventos por reglas sobre trayectorias (pase = cambio de posesión del balón, tiro = balón hacia portería, etc.).

| Requisito | Detalle |
|---|---|
| Dependencias | Python 3.12 (Oracle), `ultralytics`, torch CPU, ffmpeg; pesos YOLO (descarga pública) |
| Datos | Todo en Oracle; ningún vídeo sale del servidor |
| Coste por minuto | 0 de API; consume servidor (CPU), almacenamiento y mantenimiento |
| Límite a medir | Tiempo de proceso en CPU (4 CPU, sin GPU) frente al objetivo ≤ 3× real (ver nota en `ACCEPTANCE_CRITERIA.md`: en esta fase es objetivo, no corte) |
| Salida | Eventos + trayectorias + evidencia temporal (clip por jugada) |

Limitaciones: los eventos por reglas son frágiles en oclusiones y en resúmenes editados; la geometría (distancias, posiciones) exige calibración de campo, que se verifica aparte. **En esta fase se mide detección, seguimiento y visibilidad del balón; no se convierten trayectorias insuficientes en pases o tiros supuestamente confirmados.**

### 2. VLM por API: Qwen2.5-VL-72B-Instruct vía OpenRouter

Modelo `qwen/qwen2.5-vl-72b-instruct` en OpenRouter (verificado 2026-11-07 en `GET /api/v1/models`: modalidad `text+image->text`, entradas `text` e `image`; precio prompt 0,80 $/Mtok, completion 1,00 $/Mtok). Es un candidato concreto para establecer una primera referencia, no una garantía de precisión futbolística. Recibe fotogramas con sus tiempos explícitos y devuelve eventos en JSON.

| Requisito | Detalle |
|---|---|
| Dependencias | Clave OpenRouter como secreto del servidor (existe en el `.env` del servidor; se lee en tiempo de ejecución, nunca se copia al repo ni al chat); cliente HTTP en el backend; validador JSON (ya existe: `scripts/validate-fragment-response.py`) |
| Datos | Los fotogramas se envían al proveedor (A8: queda escrito dónde se procesan) |
| Coste por minuto | Por imagen/token; se mide y se informa (el coste no es criterio de corte) |
| Límite a medir | Tasa de peticiones, tamaño de lote de fotogramas, latencia |
| Salida | Eventos JSON + incertidumbre por dimensión |

Sobre la entrada de vídeo: que un modelo acepte vídeo nativo depende del modelo y del endpoint, no de lo que permita un CLI concreto. La prueba envía fotogramas con tiempos explícitos en cualquier caso: muestreo inicial de 1 fps y otro más denso en ventanas candidatas, seleccionadas por el sistema sin consultar la anotación.

Posible alternativa posterior: Kimi K2.5 (con capacidades visuales documentadas según el repositorio oficial de Moonshot); cualquier alternativa debe fijar modelo, versión y proveedor exactos antes de probarse. No se usa «Kimi K2 con visión» como identificación: es incorrecta o insuficiente.

## Excluidas (documentadas)

- **Muse Spark 1.3 por API (OpenCode):** no es un requisito. Vía probada el 2026-11-07 sin acceso gratuito utilizable (ver `docs/decisions/block-a-2026-11-07.md`).
- **Muse (el agente) como motor del producto:** excluido por diseño — el análisis debe ser automático, sin entregar el vídeo manualmente al agente.
- **APIs de estadísticas de partidos:** no sustituyen necesariamente el análisis de un vídeo subido; son otro producto. El coste no es una restricción, así que no se excluye nada por presupuesto.

## Plan de prueba

- **Experimentos independientes, sin dashboard completo ni híbrido todavía.**
- **Material:** fragmento B1 35-65 s primero (verificar el circuito automático), luego el clip B1 completo (explorar errores).
- **Misma puntuación:** tabla B1 de `ACCEPTANCE_CRITERIA.md`, pero **solo las categorías y ventanas suficientemente anotadas**. Los cinco eventos puntuables de B1 no permiten evaluar F1 de pases, seguimiento ni posiciones.
- **Formato común:** cada candidato produce predicciones en el esquema de `docs/evaluation/fragment-response-schema.json` (fragmento) o `annotation-schema.json` (clip completo); el validador comprueba la estructura antes de puntuar.
- **La referencia no se entrega al motor.** La comparación final se reserva para B2, después de adjudicarlo y fijar las configuraciones.
- **Trazabilidad:** se conservan configuración, predicciones originales, tiempos de ejecución, consumo y evidencia de cada resultado.
- **Regla de decisión:** gana la solución que cumple todos los umbrales de B1; si varias los cumplen, la más simple y barata de operar. Si ninguna los cumple, NO-GO o rediseño.
