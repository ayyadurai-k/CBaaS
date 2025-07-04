# Use a suitable Python base image
FROM python:3.9-slim-buster

# Set the working directory
WORKDIR /app

# Install system dependencies required for PostgreSQL client and Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev musl-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

# Copy the rest of the application code
COPY . /app

# Expose the default Django port
EXPOSE 8000

# Define the command to run the Django application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
