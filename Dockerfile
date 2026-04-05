FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (layer caching)
COPY pyproject.toml .
COPY .python-version .

# Install dependencies (no dev/test extras)
RUN uv sync --no-dev

# Copy the application code
COPY . .

EXPOSE 5000

# Run with gunicorn for production resilience
CMD ["uv", "run", "--no-dev", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "run:app"]
