# Despliegue — Soccer Forge Studio (monorepo en Oracle)

> Estado: **documentado, no ejecutado**. Los pasos de este documento son el plan de despliegue. El primer despliegue real (Fase 2 en adelante) debe ejecutarse siguiendo estos pasos y verificarse con la checklist del final. Nada de lo aquí descrito está todavía desplegado ni verificado en vivo.

## 1. Decisión

- **Monorepo, todo en el servidor Oracle.** Sin Vercel para este proyecto (desviación deliberada del estándar habitual del usuario, decidida el 2026-11-06): el procesamiento de vídeo es largo, con cola persistente y archivos grandes, y conviene que web, API, worker, base de datos y almacenamiento vivan juntos en el mismo host.
- **Repo público:** https://github.com/jpecinagithub/soccer-forge-studio — solo código y documentación. Despliegue, datos y claves, privados en el servidor.

## 2. Servidor (verificado el 2026-11-06)

| Dato | Valor verificado |
|---|---|
| Host | `iadelveloper-server` — 143.47.63.169, usuario `ubuntu` |
| SSH | `ssh -F ~/.ssh/config appforge-oracle` (clave `~/.ssh/appforge-oracle.key`, vía proxy) |
| SO / CPU / RAM | Ubuntu, 4 CPU, 23 Gi RAM (16 Gi disponibles en la comprobación) |
| Disco | 193 G total, **122 G libres** (38 % usado) — el vídeo pesa; vigilar cuota y limpieza |
| Node | v20.20.2 |
| Docker | 29.5.0 |
| ffmpeg | 6.1.1 (instalado en el host) |
| Python | 3.12.3 |
| GPU | **No detectada** (`nvidia-smi` no existe en el host). El pipeline se planifica para CPU hasta que se demuestre lo contrario; la Fase 1 debe medir tiempo/coste por minuto en CPU |
| nginx | `/etc/nginx/sites-enabled/mi-gps` — rutas existentes `/gameforge/`, `/appforge/`, `/nexus/`, `/spark/` |

Patrón que se sigue: el de GameForge — checkout en `/home/ubuntu/<proyecto>`, compose en `infra/deploy/docker-compose.yml`, proyecto compose `gameforge` → aquí `soccer-forge`. AppForge usa el mismo patrón (`/home/ubuntu/appforge`, API en `127.0.0.1:3201`).

## 3. Topología

```
Internet
  └─ https://jpecina.duckdns.org/soccer/      (nginx, única entrada pública — PROPUESTA, no configurada)
       ├─ /soccer/      → web   127.0.0.1:4310  (estático Vite, solo localhost)
       └─ /soccer/api/  → api   127.0.0.1:4300  (Node, solo localhost)
                            ├─ worker (sin puerto; consume la cola)
                            ├─ postgres (interno, sin exponer)
                            └─ redis   (interno, sin exponer; cola de trabajos)
```

Puertos elegidos (comprobados libres el 2026-11-06; en uso entonces: 3001, 3005, 3006, 3201, 3207, 3211, 3900–3902, 4000, 4120, 8081, 8444, 9443):

| Servicio | Puerto (localhost) | Público |
|---|---|---|
| web | 4310 | vía nginx `/soccer/` |
| api | 4300 | vía nginx `/soccer/api/` |
| worker | — | — |
| postgres 16 | 5432 solo red interna Docker | no |
| redis 7 | 6379 solo red interna Docker | no |

Si un puerto choca en el primer despliegue, se cambia en `infra/deploy/docker-compose.yml` y en `infra/nginx/soccer.conf` a la vez, y se anota aquí.

## 4. Servicios (docker compose)

`infra/deploy/docker-compose.yml` — proyecto `soccer-forge`:

- **web:** imagen Node 20, `npm run build` del frontend y servicio estático. Sin secretos.
- **api:** Node 20, REST + subida + biblioteca + correcciones. Lee `.env`.
- **worker:** Node 20, mismo código base que la API para el pipeline (ffmpeg + visión + eventos + Muse Spark). Sin puerto. Escala horizontal añadiendo réplicas cuando la cola lo pida.
- **postgres:** Postgres 16, volumen `soccer_pgdata`. Migraciones en `apps/api/migrations/` (pendientes de escribir en Fase 2).
- **redis:** Redis 7, volumen `soccer_redisdata`, cola persistente de trabajos.
- **Volumen de medios `soccer_media`:** originales, copias de trabajo y clips. Es el dato que más crece; no va en Git.

**Regla (lección registrada 2026-10-20): todos los servicios llevan `restart: unless-stopped`.** Sin ella, tras un reinicio del host un servicio queda parado y el resto falla en silencio.

Tras editar `.env` hay que **recrear** el contenedor (`docker compose up -d <servicio>`); un simple `restart` reutiliza el entorno viejo (lección registrada 2026-10-15).

## 5. Variables de entorno (`.env`, solo en el servidor)

Copiar `.env.example` a `.env` en el servidor y rellenarlo. **Nunca** se commitea `.env` ni ninguna clave.

| Variable | Contenido | Estado |
|---|---|---|
| `DATABASE_URL` | `postgres://soccer:***@postgres:5432/soccer` | por definir en el despliegue |
| `REDIS_URL` | `redis://redis:6379` | por definir en el despliegue |
| `STORAGE_PATH` | ruta del volumen de medios dentro del contenedor | por definir en el despliegue |
| `MUSE_SPARK_API_KEY` | clave de acceso a Muse Spark 1.3 | **PENDIENTE — nombre, proveedor y endpoint por confirmar en Fase 1** |
| `MUSE_SPARK_MODEL` | `muse-spark-1.3` | por confirmar en Fase 1 |
| `MUSE_SPARK_BASE_URL` | endpoint de la API | **PENDIENTE de confirmar** |
| `PUBLIC_BASE_URL` | `https://jpecina.duckdns.org/soccer` | propuesta |

Las claves se verifican con una llamada real antes de anunciar que funcionan; una línea en un fichero no es una verificación.

## 6. Pasos del primer despliegue

Ejecutar en el servidor, en orden. Cada paso deja evidencia (salida del comando) antes de pasar al siguiente.

1. **Clonar:** `git clone https://github.com/jpecinagithub/soccer-forge-studio.git ~/soccer-forge-studio` (o `git pull` si ya existe; comprobar antes que no haya cambios sin commitear en el checkout del servidor).
2. **Entorno:** copiar `.env.example` a `.env` en `~/soccer-forge-studio` y rellenar valores. No pegar claves en el chat.
3. **Construir:** `cd ~/soccer-forge-studio/infra/deploy && docker compose build` — leer el log entero; cualquier error de build es un despliegue fallido aunque en local compile.
4. **Base de datos:** `docker compose up -d postgres redis` y esperar a los healthchecks; luego migraciones (`docker compose run --rm api npm run migrate` — comando exacto por definir en Fase 2).
5. **Levantar todo:** `docker compose up -d` y comprobar `docker compose ps` (todos `Up` y sanos).
6. **nginx:** copiar `infra/nginx/soccer.conf` como bloque `location` en `/etc/nginx/sites-enabled/mi-gps` (siguiendo el patrón de `/appforge/`), `sudo nginx -t` y `sudo systemctl reload nginx`.
7. **Humo:** abrir `https://jpecina.duckdns.org/soccer/` en el navegador, subir un clip corto y comprobar que el trabajo aparece en la cola y termina (ver checklist).
8. **Copia de seguridad:** definir y probar el backup de `soccer_pgdata` + `soccer_media` antes de dar el despliegue por bueno (frecuencia y restauración pendientes; el vídeo no se respalda dos veces por accidente).

## 7. nginx (propuesta)

`infra/nginx/soccer.conf` — fragmento a integrar en `mi-gps`, mismo patrón que `/appforge/`:

```nginx
location /soccer/ {
    proxy_pass http://127.0.0.1:4310/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 2G;  # subida de vídeo; ajustar en Fase 2
}

location /soccer/api/ {
    proxy_pass http://127.0.0.1:4300/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 2G;
    proxy_read_timeout 300s;  # las respuestas del análisis pueden tardar
}
```

Notas: `client_max_body_size` y los timeouts son valores iniciales; la Fase 2 (ingesta) debe ajustarlos con pruebas reales de subida. No exponer jamás los puertos 4300/4310/5432/6379 a internet: solo localhost + nginx.

## 8. Actualizaciones posteriores

1. `git pull` en `~/soccer-forge-studio` (resolver antes cualquier cambio sin commitear; no se despliega con el árbol sucio).
2. `docker compose build` y `docker compose up -d <servicio>` (recrear, no solo reiniciar, si cambió `.env`).
3. Migraciones si las hay, antes de levantar la API nueva.
4. Verificación de humo (checklist) y anotación del commit desplegado en el registro de despliegues (pendiente de crear: `docs/DEPLOY_LOG.md`).

## 9. Copia de seguridad y recuperación

- **Qué se respalda:** volumen `soccer_pgdata` (partidos, eventos, correcciones) + `soccer_media` (originales, clips). La cola de Redis se reconstruye desde la base de datos; un trabajo a medias se reencola, no se inventa su resultado.
- **Qué NO se respalda en Git:** vídeos, `.env`, bases de datos.
- **Restauración:** procedimiento y prueba de restauración pendientes de escribir en la Fase 2. Un backup sin prueba de restauración no cuenta.

## 10. Checklist de verificación (antes de anunciar un despliegue como hecho)

Adaptada de la práctica del equipo; ejecutar contra la URL pública, no contra localhost del servidor:

- [ ] Build del compose limpio, log leído entero.
- [ ] Todos los servicios `Up` (y sanos donde haya healthcheck), con `restart: unless-stopped`.
- [ ] `https://jpecina.duckdns.org/soccer/` carga la app.
- [ ] Subida de un clip corto aceptada; el trabajo pasa por sus etapas visibles.
- [ ] El trabajo termina (o falla con un mensaje claro) y el dashboard muestra sus jugadas con evidencia que abre el fragmento exacto.
- [ ] Una corrección del usuario persiste tras recargar.
- [ ] Migraciones aplicadas en la base de datos real; ninguna página depende de datos de prueba.
- [ ] Clave de Muse Spark verificada con una llamada real (cuando exista la integración).
- [ ] Backup definido y restauración probada (desde la Fase 2).

Si algo de la lista falla, el despliegue no se anuncia como hecho: se anota el fallo, se corrige la checklist y se vuelve a verificar.
