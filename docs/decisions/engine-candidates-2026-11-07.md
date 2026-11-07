# Motores candidatos para el análisis de vídeo — propuesta (2026-11-07)

Decisión del usuario 2026-11-07: Muse de Meta es el agente de desarrollo; el motor que analizará los vídeos dentro de la aplicación está **pendiente de selección mediante pruebas**. No se exige Muse Spark ni una API concreta. El producto debe ejecutar el análisis automáticamente (vídeo subido → procesamiento → jugadas con evidencia → dashboard), sin entregar el vídeo manualmente al agente Muse.

## Candidatos

### 1. Pipeline CV local: YOLO + seguimiento + reglas

Detección de jugadores y balón (Ultralytics YOLO), seguimiento (ByteTrack/BoT-SORT), calibración del campo por homografía y eventos por reglas sobre trayectorias (pase = cambio de posesión del balón, tiro = balón hacia portería, etc.).

| Requisito | Detalle |
|---|---|
| Dependencias | Python 3.11+, `ultralytics`, torch CPU, ffmpeg; pesos YOLO (descarga pública) |
| Datos | Todo en Oracle; ningún vídeo sale del servidor |
| Coste por minuto | 0 (sin API) |
| Límite a medir | Tiempo de proceso en CPU (4 CPU, sin GPU verificada) frente al umbral ≤ 3× real |
| Salida | Eventos + trayectorias + evidencia temporal (clip por jugada) |

Limitaciones: los eventos por reglas son frágiles en oclusiones y en resúmenes editados; la geometría (distancias, posiciones) exige calibración de campo, que se verifica aparte.

### 2. VLM por API: fotogramas como imágenes

Un modelo de visión-lenguaje (p. ej. Qwen2.5-VL o Kimi K2 con visión) recibe fotogramas muestreados (1 fps) y devuelve eventos en JSON. Vía Top Tools AI (gateway ya verificado 2026-11-06) u OpenRouter.

| Requisito | Detalle |
|---|---|
| Dependencias | Clave API como secreto del servidor; cliente HTTP en el backend; validador JSON (ya existe: `scripts/validate-fragment-response.py`) |
| Datos | Los fotogramas se envían al proveedor (A8: queda escrito dónde se procesan) |
| Coste por minuto | Por imagen/token; se mide y se informa (no es criterio de corte) |
| Límite a medir | Tasa de peticiones, tamaño de lote de fotogramas, latencia |
| Salida | Eventos JSON + incertidumbre por dimensión |

Limitaciones: sin entrada de vídeo nativa (comprobado con el CLI: solo imágenes); coste por minuto; riesgo de tiempos inventados — se valida contra el esquema y la referencia.

### 3. Híbrido: CV + VLM

El pipeline CV propone candidatos (jugadas, tiempos, trayectorias) y el VLM revisa solo los casos ambiguos y redacta explicaciones. Solo se considera si 1 o 2 se quedan cortos; es la opción más compleja.

## Excluidas (documentadas)

- **Muse Spark 1.3 por API (OpenCode):** no es un requisito. Vía probada el 2026-11-07 sin acceso gratuito utilizable (ver `docs/decisions/block-a-2026-11-07.md`).
- **Muse (el agente) como motor del producto:** excluido por diseño — el análisis debe ser automático, sin entregar el vídeo manualmente al agente.
- **APIs comerciales de datos deportivos:** fuera de alcance por coste (proyecto educativo).

## Plan de prueba (cuando el usuario elija)

- **Mismo material para todos:** fragmento B1 35-65 s primero, luego el clip B1 completo; referencia v2 (exploratoria, para desarrollo).
- **Misma puntuación:** tabla B1 de `ACCEPTANCE_CRITERIA.md` (F1 de pases/tiros, error mediano de jugada, tiempo de proceso, coste por minuto) + comprobación de que cada jugada abre su evidencia.
- **Formato común:** cada candidato produce predicciones en el esquema de `docs/evaluation/fragment-response-schema.json` (fragmento) o `annotation-schema.json` (clip completo); el validador comprueba la estructura antes de puntuar.
- **Comparación final:** sobre el clip reservado B2 con su referencia adjudicada; la referencia nunca es la salida de una de las soluciones comparadas.
- **Regla de decisión:** gana la solución que cumple todos los umbrales de B1; si varias los cumplen, la más simple y barata de operar. Si ninguna los cumple, NO-GO o rediseño.
