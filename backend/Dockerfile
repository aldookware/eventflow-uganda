FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create directories for media and static files
RUN mkdir -p /app/media /app/staticfiles /app/logs

# Collect static files (will be overridden in docker-compose)
RUN python manage.py collectstatic --noinput || true

# Create a non-root user
RUN groupadd -r eventflow && useradd -r -g eventflow eventflow
RUN chown -R eventflow:eventflow /app
USER eventflow

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/ || exit 1

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Development stage
FROM base as development
# Remove the user creation for development to allow file modifications
USER root
RUN chown -R root:root /app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]