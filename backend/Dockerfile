FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY pytest.ini ./

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Initialize schema and seed via one-time init command, then serve the API.
CMD ["sh", "-c", "python -m app.core.init_db || true; uvicorn app.main:app --host 0.0.0.0 --port 8000"]
