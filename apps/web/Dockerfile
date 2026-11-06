# Fase 0: esqueleto. El frontend aún no está implementado (Fase 5); este Dockerfile
# documenta la forma de construirlo cuando exista src + build de Vite.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
COPY apps/web/package.json apps/web/
COPY packages/shared/package.json packages/shared/
RUN npm install --workspaces --include-workspace-root || true
COPY . .
RUN npm run build -w @soccer-forge/web

FROM nginx:alpine
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
EXPOSE 80
