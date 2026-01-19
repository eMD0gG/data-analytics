FROM python:3.12-slim

RUN pip install --no-cache-dir psycopg2-binary python-dotenv

WORKDIR /app
COPY data_generator.py ./
COPY .env ./

CMD ["python", "data_generator.py"]
