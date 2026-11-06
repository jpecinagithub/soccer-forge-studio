# Fase 0: esqueleto. El worker aún no está implementado (Fase 2); este Dockerfile
# documenta la forma de construirlo cuando exista src + build.
# ffmpeg se instala aquí porque el worker lo usa para preparar y trocear vídeo.
FROM node:20-alpine
RUN apk add --no-cache ffmpeg
WORKDIR /app
COPY package.json ./
COPY apps/worker/package.json apps/worker/
COPY packages/shared/package.json packages/shared/
RUN npm install --workspaces --include-workspace-root || true
COPY . .
RUN npm run build -w @soccer-forge/worker
CMD ["node", "apps/worker/dist/index.js"]
