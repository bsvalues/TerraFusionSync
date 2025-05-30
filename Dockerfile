FROM python:3.11-alpine

LABEL maintainer="TerraFusion Team"
LABEL description="TerraFusion Platform - Enterprise County Government GIS Platform"
LABEL version="2.0.0"

WORKDIR /app

RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    musl-dev \
    curl \
    && rm -rf /var/cache/apk/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser -D -s /bin/sh terrafusion && \
    chown -R terrafusion:terrafusion /app

USER terrafusion

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "60", "main:app"]