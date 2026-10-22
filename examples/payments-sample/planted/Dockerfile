# payments-sample API — PLANTED variant.
# PLANTED FLAW #4 (see PLANTED.md): the base image is a frozen April-2022
# snapshot (CPython 3.10.4 on Debian bullseye, OpenSSL 1.1.1n) that carries
# years of known, fixed-elsewhere vulnerabilities (e.g. CVE-2022-1292 in
# OpenSSL 1.1.1n, CVE-2022-45061 in CPython < 3.10.9) and never receives
# patches. Expected to be caught by the container scanning gate
# (blueprint gate 5). The clean variant uses a current maintained image.
FROM python:3.10.4-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["python", "app.py"]
