FROM python:3.11-slim

WORKDIR /app

# Install dependencies (quote version specifiers — bare >= is a shell redirect)
RUN pip install --no-cache-dir \
    "mcp>=1.25.0" \
    "httpx>=0.28.0" \
    "python-dotenv>=1.0.0" \
    "starlette" \
    "uvicorn[standard]"

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
