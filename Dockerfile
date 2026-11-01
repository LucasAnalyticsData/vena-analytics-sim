FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/mock_api ./src/mock_api

ENV PORT=8080
CMD exec uvicorn src.mock_api.main:app --host 0.0.0.0 --port $PORT