FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY config.py .
COPY main.py .

RUN mkdir -p /app/pdfs /app/images && \
    chmod 777 /app/pdfs /app/images

ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

CMD ["python", "main.py"] 