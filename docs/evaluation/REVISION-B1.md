# Revisión independiente de B1 — 2026-11-06

## Alcance y método
Se revisó el JSON adjunto B1-georgia-espana-annotation.json y el vídeo local georgia-espana-rfef.mp4. Se consultaron el diccionario, el contrato, los criterios de aceptación y la plantilla en el commit 91e96aa mediante el conector GitHub. No se ha comparado byte a byte el adjunto con el JSON del repositorio.

Muestra principal: play-B, play-F y play-H2 (3/9 = 33,3 %), mediante secuencias de fotogramas a 4 fps. Se amplió la inspección a play-G para resolver la repetición y a la terminación de play-H. No es una revisión exhaustiva del clip. Revisor: asistente de IA; no sustituye la adjudicación humana. Tiempos propuestos aproximados: requieren ajuste al fotograma antes de fijarlos como referencia exacta.

## Hallazgos prioritarios

### 1. play-H2 duplica el cuarto gol
El tramo aproximadamente 153–157 s muestra de nuevo el gol de Oyarzabal desde otra cámara; 157–163 s muestra otra repetición. La comparación con 145–146 s y la celebración de 149–151 s confirma que corresponde a play-G.
Corrección: eliminar play-H2 y ev-H2-1 del catálogo de acciones nuevas; reclasificar 153–157 como replay; cambiar replayOfPlayId de 157–163 a play-G. Refinar los cortes exactos. Esta corrección sola deja 8 jugadas y 11 eventos; no constituye un recuento final validado.
Evidencia: H2.jpg y checks.jpg.

### 2. play-B: minuto del penalti incorrecto
En 43,5–46,75 s el reloj avanza aproximadamente de 10:30 a 10:33. El rótulo de 50–50,5 s dice OYARZABAL (11'), no 13:11.
Corrección: sustituir la nota del minuto 13 por minuto 11. matchClockStart debe reflejar el reloj al inicio adoptado para la jugada, no el minuto nominal del gol. El golpeo se sitúa aproximadamente en 45,5–45,75 s; el desenlace, alrededor de 46–46,25 s. Revisar el actual intervalo 44,8–45,8. El cambio de primer plano a campo ocurre cerca de 43,5 s, dentro de la tolerancia declarada de la segmentación inicial.
Evidencia: B.jpg y B-caption.jpg.

### 3. play-F: acción y tiempos incorrectos
En 120,25–125,5 s se ve juego abierto, una entrega hacia el área, un balón que sale hacia la frontal y un disparo con el pie que recoge el portero. No respalda la descripción de falta lateral y remate de cabeza.
Corrección: describir disparo desde fuera del área, resultado saved; mantener el rematador desconocido si el dorsal no se verifica. El golpeo está aproximadamente en 123–123,5 s, antes de tStart=124,8. Ajustar el final al control del portero, no al primer plano posterior. El reloj es visible: alrededor de 59:47 al comienzo y 59:50 al tiro. Eliminar la nota que dice que no es visible. La primera imagen en 120 s aún pertenece a la repetición anterior: ajustar el corte aproximadamente 120–120,25 s.
Evidencia: F.jpg y F-contact.jpg.

### 4. play-H: intervalo del posible remate tardío
A 210 s ya se observa una acción de remate junto al portero; en 212–213 s la acción está terminando y los jugadores se separan. El intervalo actual 212–213 no captura el contacto inicial.
Corrección: revisar a mayor frecuencia 209–211 s y determinar el resultado sin inferirlo. No se propone aquí identidad ni resultado definitivo.
Evidencia: late.jpg.

## Coherencia del archivo y del protocolo
- Confirmados 39 segmentos, 9 jugadas y 12 eventos. Tipos de segmento: 16 field-view, 14 close-up, 7 replay y 2 excluded. Cubren 0–237,24 s sin huecos ni solapamientos numéricos. Esto no valida las etiquetas visuales.
- Los 12 eventos tienen uncertain=true, aunque solo 5 jugadas lo tienen. Separar incertidumbre de tipo, identidad, resultado y tiempo; adjudicar los campos comprobados. No basta con cambiar todos los booleanos a false.
- Los posibles tiros A/H no deben tratarse como tiros confirmados para puntuar. Definir una máscara explícita de casos pendientes/no puntuables antes de ejecutar ambos sistemas.
- Anotación parcial: faltan pases de elaboración, pérdidas y recuperaciones. No usarla para F1 global de esas clases: detecciones correctas no anotadas producirían falsos positivos artificiales. Completar ventanas seleccionadas de forma exhaustiva y fijar qué intervalos y categorías se puntúan.
- Este fichero sigue la plantilla simplificada; no se exige que sea una instancia completa del contrato de producción. Sí hace falta un esquema verificable para la anotación, referencia inequívoca al vídeo (idealmente SHA256) y trazabilidad de revisión. El texto descriptivo en $schema no es un JSON Schema ejecutable.
- matchClockStart no debe convertirse de un rótulo 22', 24' o 63' a 22:00, 24:00 o 63:00. El rótulo es minuto nominal del gol, no reloj exacto de inicio. En G se ve 62:29–62:30 durante el remate, aunque el rótulo indique 63'. Leer el reloj del inicio o dejar null y conservar el minuto en un campo/nota separado.
- field-view suma 136 s (57,33 %) antes de corregir H2. El requisito de >=70 % de tiempo analizable sobre toda la duración es incompatible con esta segmentación si solo el campo cuenta como analizable. Separar cobertura de observación del clip de cobertura lograda sobre material elegible; registrar cualquier cambio de criterio antes del ensayo. Vista de campo tampoco acredita calibración.
- ACCEPTANCE_CRITERIA describe F1 como aciertos/(omisiones+falsos positivos): corregir a 2TP/(2TP+FP+FN), con emparejamiento uno a uno y tratamiento explícito de participantes desconocidos.
- No llamar a esta referencia anotación humana validada: el propio archivo atribuye el primer pase a Muse. Esta segunda revisión también es de IA y solo cubre una muestra. Hace falta adjudicación humana, especialmente al evaluar el mismo modelo que generó las etiquetas.

## Dictamen
Necesita correcciones antes de usarse como referencia para el bloque B de viabilidad. El bloque A de acceso técnico puede avanzar de manera independiente. Conservar este primer pase y registrar las correcciones en una nueva versión. No se han modificado el JSON original ni el repositorio.
