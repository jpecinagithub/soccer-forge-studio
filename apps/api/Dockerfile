# Fase 0: esqueleto. La app aún no está implementada (Fase 2); este Dockerfile
# documenta la forma de construirla cuando exista src + build.
FROM node:20-alpine
WORKDIR /app
COPY package.json ./
COPY apps/api/package.json apps/api/
COPY packages/shared/package.json packages/shared/
RUN npm install --workspaces --include-workspace-root || true
COPY . .
RUN npm run build -w @soccer-forge/api
EXPOSE 4300
CMD ["node", "apps/api/dist/index.js"]
