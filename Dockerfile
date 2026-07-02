FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask flask-sqlalchemy flask-login flask-migrate flask-wtf email-validator python-dotenv gunicorn

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]