# Playwright needs Chromium + system libs. The official Playwright Python image
# ships them preinstalled and matches our playwright>=1.60 pin.
FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

LABEL org.opencontainers.image.title="Windows Copilot API"
LABEL org.opencontainers.image.description="OpenAI-compatible API for Microsoft Copilot"

WORKDIR /app

# Install Python deps first so the layer caches across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium

COPY . .

# Serve on all interfaces inside the container; map the port in compose.
ENV HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/models')" || exit 1

CMD ["python", "app.py"]
