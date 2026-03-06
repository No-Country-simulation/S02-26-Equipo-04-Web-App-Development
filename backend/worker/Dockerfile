FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# ---- SYSTEM DEPENDENCIES ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libsm6 \
    libxext6 \
    libgl1 \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ---- PYTHON DEPENDENCIES ----
COPY requirements.txt ./requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch==2.1.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir openai-whisper==20250625 numpy>=1.25.0 && \
    pip install --no-cache-dir -r requirements.txt

# ---- APP CODE ----
COPY . .

# ---- SECURITY ----
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ---- HEALTHCHECK ----
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import redis, os; redis.Redis(host=os.getenv('REDIS_HOST','redis')).ping()" || exit 1

CMD ["python", "app/worker.py"]