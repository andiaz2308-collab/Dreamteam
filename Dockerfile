FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-spa \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY frontend ./frontend

ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
