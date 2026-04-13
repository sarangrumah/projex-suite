FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine
RUN addgroup -S appuser && adduser -S appuser -G appuser
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["wget", "-q", "-O-", "http://localhost:3000"]
CMD ["serve", "-s", "dist", "-l", "3000"]
