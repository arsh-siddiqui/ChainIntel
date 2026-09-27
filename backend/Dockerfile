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

# Create tables on startup (use Alembic migrations for production upgrades), then serve the API.
CMD ["sh", "-c", "python -c 'from app.core.database import init_db; init_db()' || true; uvicorn app.main:app --host 0.0.0.0 --port 8000"]
