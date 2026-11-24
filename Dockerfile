FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
RUN useradd -m -u 1000 user
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY --chown=user:user Flask/ /app/Flask/
USER user
EXPOSE 7860
CMD ["gunicorn", "--chdir", "/app/Flask", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "2", "--timeout", "120", "app:app"]
