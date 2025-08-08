FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \ 
    DJANGO_ENV=prod
WORKDIR /app
COPY requirements/prod.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
CMD ["bash", "-lc", "python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]