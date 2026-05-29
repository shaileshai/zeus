FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY fivetran_pyproject.toml pyproject.toml
RUN pip install --no-cache-dir mcp>=1.25.0 httpx>=0.28.0 python-dotenv>=1.0.0 \
    starlette uvicorn

# Copy server source and API definitions
COPY server.py .
COPY http_server.py .
COPY fivetran-open-api-definition.json .
COPY open-api-definitions/ ./open-api-definitions/

# Environment configuration
ENV FIVETRAN_ALLOW_WRITES=true
ENV PORT=8080

EXPOSE 8080

CMD ["python", "http_server.py"]
