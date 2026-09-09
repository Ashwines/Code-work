FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir psycopg2-binary faker

COPY seed_retail_db.py .

CMD ["python", "seed_retail_db.py"]