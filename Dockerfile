FROM python:3.12-slim AS build

WORKDIR /app

COPY pyproject.toml README.md ./
COPY memcp/ memcp/

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

FROM python:3.12-slim

WORKDIR /app

RUN adduser --disabled-password --gecos "" memcp

COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin/memcp /usr/local/bin/memcp

USER memcp

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health',timeout=5).status==200 else 1)" \
    || exit 1

ENTRYPOINT ["python", "-m", "memcp"]
