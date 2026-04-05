# URL Shortener — Production Engineering Hackathon

A resilient URL shortener service built for the **MLH Production Engineering Hackathon**. This project demonstrates production-grade reliability engineering practices including automated testing, CI/CD gating, graceful error handling, and chaos-resilient containerization.

**Stack:** Flask · Peewee ORM · PostgreSQL · Docker · GitHub Actions · pytest

---

## 🏆 Quest: Reliability Engineering — Gold Tier

| Tier | Requirement | Status |
|------|------------|--------|
| 🥉 Bronze | Unit tests + CI + `/health` endpoint | ✅ |
| 🥈 Silver | >50% coverage + integration tests + blocked deploys | ✅ (81%) |
| 🥇 Gold | >70% coverage + graceful errors + chaos resilience | ✅ |

---

## Quick Start

### Local Development (with uv)

```bash
# 1. Install dependencies
uv sync --extra test

# 2. Configure environment
cp .env.example .env   # edit if your DB credentials differ

# 3. Run the server
uv run run.py

# 4. Verify
curl http://localhost:5000/health
# → {"status":"ok"}
```

### Docker (Production)

```bash
# Start the full stack (app + PostgreSQL)
docker-compose up --build -d

# Verify
curl http://localhost:5000/health

# Chaos test: kill the app — watch it resurrect
docker kill url-shortener
docker ps  # It comes back automatically (restart: always)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — returns `200 OK` |
| `POST` | `/shorten` | Shorten a URL |
| `GET` | `/<short_code>` | Redirect to the original URL |
| `GET` | `/urls` | List all shortened URLs |

### Example: Shorten a URL

```bash
curl -X POST http://localhost:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

Response:
```json
{
  "short_code": "aB3xYz",
  "original_url": "https://example.com",
  "short_url": "http://localhost:5000/aB3xYz",
  "created_at": "2026-04-05T12:00:00"
}
```

---

## Testing

```bash
# Run all tests with coverage
uv run pytest

# Run tests verbosely without coverage
uv run pytest --no-cov -v
```

### Test Coverage: 81%

- **Unit Tests** (`tests/test_units.py`): Test `generate_short_code()` and `is_valid_url()` in isolation.
- **Integration Tests** (`tests/test_integration.py`): Full API tests using Flask's test client and in-memory SQLite.

---

## CI/CD

GitHub Actions runs on every push and pull request:

1. **Spins up a PostgreSQL service** container
2. **Installs dependencies** via `uv`
3. **Runs the full test suite** with coverage
4. **Blocks the pipeline** if any test fails or coverage drops below 70%

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Reliability Features

### Graceful Error Handling
All errors return clean JSON responses — never raw HTML or Python stack traces.

### Chaos Resilience
The Docker setup uses `restart: always` on both the app and database. Kill either container and it auto-restarts within seconds.

### Input Validation
Every request is validated before touching the database. Invalid URLs, missing fields, and bad short codes all return descriptive `400` errors.

---

## Documentation

- [`docs/ERROR_HANDLING.md`](docs/ERROR_HANDLING.md) — How the app handles 400, 404, 405, and 500 errors
- [`docs/FAILURE_MODES.md`](docs/FAILURE_MODES.md) — What happens when things break (and how they recover)

---

## Project Structure

```
pehackathon/
├── app/
│   ├── __init__.py              # App factory with global error handlers
│   ├── database.py              # DatabaseProxy, BaseModel, connection hooks
│   ├── models/
│   │   ├── __init__.py          # Model registration
│   │   └── url.py               # ShortenedURL model + short code generator
│   └── routes/
│       ├── __init__.py          # Blueprint registration
│       └── shortener.py         # URL shortener API endpoints
├── tests/
│   ├── conftest.py              # pytest configuration
│   ├── test_units.py            # Unit tests (no DB)
│   └── test_integration.py     # Integration tests (in-memory SQLite)
├── docs/
│   ├── ERROR_HANDLING.md        # Error handling documentation
│   └── FAILURE_MODES.md         # Failure modes documentation
├── .github/workflows/ci.yml    # CI pipeline
├── Dockerfile                   # Production container
├── docker-compose.yml           # Full stack with restart policies
├── pyproject.toml               # Dependencies + test config
└── run.py                       # Entry point
```
