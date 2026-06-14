FROM python:3.12-slim AS base

WORKDIR /app

RUN adduser --disabled-password --gecos "" memcp

COPY pyproject.toml README.md ./
COPY memcp/ memcp/

RUN pip install --no-cache-dir .

USER memcp

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health',timeout=5).status==200 else 1)" \
    || exit 1

ENTRYPOINT ["python", "-m", "memcp"]
