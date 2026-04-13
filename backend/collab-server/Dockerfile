FROM node:22-alpine
RUN addgroup -S appuser && adduser -S appuser -G appuser
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --production
COPY src/ ./src/
USER appuser
EXPOSE 8400
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["wget", "-q", "-O-", "http://localhost:8400/health"]
CMD ["node", "src/index.js"]
