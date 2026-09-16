FROM node:22-slim

WORKDIR /app
RUN corepack enable

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

ENV PORT=8443
ENV FIGMA_DEV_SERVER_HOST=0.0.0.0
EXPOSE 8443

CMD ["pnpm", "dev"]
