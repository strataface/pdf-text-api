# PDF Text & Tables API. ~512 MB RAM is enough for 1-2 concurrent OCR jobs at the default limits.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu tesseract-ocr-fra tesseract-ocr-spa \
      tesseract-ocr-ita tesseract-ocr-por tesseract-ocr-chi-sim tesseract-ocr-jpn \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_THREAD_LIMIT=1 PORT=8000
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
RUN useradd -m -u 1000 user
USER user
EXPOSE 8000
# $PORT is honoured (Render/Cloud Run/Koyeb/HF Spaces set it; HF expects 7860 via app_port).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --no-access-log --proxy-headers --forwarded-allow-ips='*'"]
