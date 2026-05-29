FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "google-adk>=2.1.0" \
    "mcp>=1.0" \
    "google-cloud-bigquery>=3.20" \
    "google-cloud-secret-manager>=2.20" \
    "fastapi>=0.110" \
    "uvicorn[standard]>=0.29" \
    "httpx>=0.27" \
    "python-dotenv>=1.0" \
    "sse-starlette>=2.0" \
    "starlette>=0.27"

# Copy all source
COPY agent/ ./agent/
COPY mcp_server/server.py ./mcp_server/server.py
COPY mcp_server/open-api-definitions/ ./mcp_server/open-api-definitions/
COPY mcp_server/fivetran-open-api-definition.json ./mcp_server/
COPY web/ ./web/

ENV WEB_PORT=8080
EXPOSE 8080

CMD ["python", "web/server.py"]
