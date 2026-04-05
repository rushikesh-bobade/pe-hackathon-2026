FROM python:3.13-slim

# Install curl for healthcheck and uv for dependency management
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (layer caching)
COPY pyproject.toml .
COPY .python-version .

# Install dependencies (no dev/test extras)
RUN uv sync --no-dev

# Copy the application code + CSV seed files
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

EXPOSE 5000

# Entrypoint: seed DB → start gunicorn
CMD ["./entrypoint.sh"]
