FROM python:3.11-slim

WORKDIR /app

# Install dependencies straight from pyproject (reproducible, pins google-adk).
# Copy the package source first so the `agent` wheel can build.
COPY pyproject.toml README.md ./
COPY agent/ ./agent/
RUN pip install --no-cache-dir .

# Fivetran MCP server (run in-process over stdio by the agent) + its API schemas.
COPY mcp_server/server.py ./mcp_server/server.py
COPY mcp_server/open-api-definitions/ ./mcp_server/open-api-definitions/
COPY mcp_server/fivetran-open-api-definition.json ./mcp_server/

# Web server + static UI.
COPY web/ ./web/

# Cloud Run injects $PORT (defaults to 8080); the server reads it via config.
EXPOSE 8080

CMD ["python", "web/server.py"]
