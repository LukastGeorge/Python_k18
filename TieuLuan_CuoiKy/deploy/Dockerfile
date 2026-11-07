FROM python:3.12-slim

ARG VCS_REF=local
ARG SOURCE_URL=https://github.com/LukastGeorge/Python_k18
LABEL org.opencontainers.image.title="TieuLuan CuoiKy Real Estate AI" \
      org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.revision="${VCS_REF}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    DB_BACKEND=sqlite \
    OPENBLAS_NUM_THREADS=1 \
    OMP_NUM_THREADS=2

WORKDIR /app
RUN apt-get update \
    && apt-get install --yes --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app

COPY requirements/base.txt requirements/production.txt ./requirements/
RUN python -m pip install --no-cache-dir -r requirements/production.txt \
    && python -m pip check

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY data/raw/kc_house_data.csv ./data/raw/kc_house_data.csv
COPY data/raw/kaggle_vietnam_2024/ ./data/raw/kaggle_vietnam_2024/
COPY data/context/ ./data/context/
COPY artifacts/kingcounty/charts/ ./artifacts/kingcounty/charts/
COPY artifacts/vietnam/ ./artifacts/vietnam/
COPY pytest.ini ./pytest.ini
RUN python -m backend.train_kingcounty
RUN mkdir -p /app/storage /app/models \
    && chown app:app /app/storage /app/models

USER 10001:10001
VOLUME ["/app/storage", "/app/models"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; r = urllib.request.urlopen('http://127.0.0.1:8000/api/status', timeout=3); assert r.status == 200"]

CMD ["waitress-serve", "--host=0.0.0.0", "--port=8000", "--threads=4", "--call", "backend.web_app:create_app"]
