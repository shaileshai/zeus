FROM node:20-slim

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci --production

# Copy source and build
COPY . .
RUN npm run build 2>/dev/null || true

# Environment configuration
ENV FIVETRAN_ALLOW_WRITES=true
ENV MCP_TRANSPORT=sse
ENV PORT=8080

EXPOSE 8080

CMD ["node", "dist/index.js"]
