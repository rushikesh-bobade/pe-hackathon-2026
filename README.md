# ShieldURL — Chaos-Resilient URL Shortener

[![CI — Test & Coverage](https://github.com/rushikesh-bobade/pe-hackathon-2026/actions/workflows/ci.yml/badge.svg)](https://github.com/rushikesh-bobade/pe-hackathon-2026/actions/workflows/ci.yml)
![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Gold Tier](https://img.shields.io/badge/quest-Gold%20Tier-gold)

A resilient URL shortener service built for the **MLH Production Engineering Hackathon 2026**. This project demonstrates production-grade reliability engineering practices including automated testing, CI/CD gating, graceful error handling, idempotent database seeding, and chaos-resilient containerization.

**Stack:** Flask · Peewee ORM · PostgreSQL · SQLite · Docker · GitHub Actions · pytest

---

## Quest: Reliability Engineering — Gold Tier

| Tier | Requirement | Status |
|------|------------|--------|
| Bronze | Unit tests + CI + `/health` endpoint | Done |
| Silver | >50% coverage + integration tests + blocked deploys | Done (85%) |
| Gold | >70% coverage + graceful errors + chaos resilience | Done (85%) |

---

## Quick Start

### Local Development (no PostgreSQL needed)

```bash
# 1. Clone the repo
git clone https://github.com/rushikesh-bobade/pe-hackathon-2026.git
cd pe-hackathon-2026

# 2. Install dependencies
uv sync --extra test

# 3. Configure environment
cp .env.example .env

# 4. Seed the database (idempotent — safe to run multiple times)
uv run seed.py

# 5. Run the server
uv run run.py

# 6. Verify
curl http://localhost:5000/health
# → {"status":"ok"}
```

### Docker (Production)

```bash
# Start the full stack (app + PostgreSQL + auto-seeding)
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
| `GET` | `/users` | List all users |
| `GET` | `/users/<id>` | Get a single user by ID |
| `GET` | `/events` | List all events (filterable by `url_id`, `user_id`) |
| `GET` | `/events/<id>` | Get a single event by ID |

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

## Database Seeding

The project includes an idempotent seed script that loads MLH-provided CSV data:

```bash
uv run seed.py
```

- Loads `users.csv`, `urls.csv`, `events.csv` in foreign key order
- Safe to run multiple times — checks if data exists before inserting
- Runs automatically on Docker container startup via `entrypoint.sh`

---

## Testing

```bash
# Run all tests with coverage
uv run pytest

# Run tests verbosely without coverage
uv run pytest --no-cov -v
```

### Test Coverage: 85%

- **59 total tests** (16 unit + 43 integration)
- **Unit Tests** (`tests/test_units.py`): Test `generate_short_code()` and `is_valid_url()` in isolation
- **Integration Tests** (`tests/test_integration.py`): Full API tests using Flask test client and in-memory SQLite

---

## CI/CD

GitHub Actions runs on every push and pull request:

1. Spins up a PostgreSQL service container
2. Installs dependencies via `uv`
3. Runs the full test suite with coverage
4. Blocks the pipeline if any test fails or coverage drops below 70%

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Reliability Features

### Graceful Error Handling
All errors return clean JSON responses — never raw HTML or Python stack traces. Global handlers for 400, 404, 405, and 500 errors.

### Chaos Resilience
The Docker setup uses `restart: always` on both the app and database. Kill either container and it auto-restarts within seconds.

### Input Validation
Every request is validated before touching the database. Invalid URLs, missing fields, and bad short codes all return descriptive `400` errors.

### Idempotent Seeding
The `seed.py` script checks if tables already have data before inserting, preventing duplicates on repeated runs — an SRE best practice for zero-touch deployments.

---

## Documentation

- [`docs/ERROR_HANDLING.md`](docs/ERROR_HANDLING.md) — How the app handles 400, 404, 405, and 500 errors
- [`docs/FAILURE_MODES.md`](docs/FAILURE_MODES.md) — What happens when things break (and how they recover)

---

## Project Structure

```
pe-hackathon-2026/
├── app/
│   ├── __init__.py              # App factory with global error handlers
│   ├── database.py              # DatabaseProxy, BaseModel, SQLite/Postgres support
│   ├── models/
│   │   ├── __init__.py          # Model registration
│   │   ├── user.py              # User model
│   │   ├── url.py               # ShortenedURL model + short code generator
│   │   └── event.py             # Event/analytics model
│   └── routes/
│       ├── __init__.py          # Blueprint registration
│       ├── shortener.py         # URL shortener + redirect endpoints
│       ├── users.py             # User API endpoints
│       └── events.py            # Event API endpoints
├── tests/
│   ├── conftest.py              # pytest configuration
│   ├── test_units.py            # Unit tests (no DB)
│   └── test_integration.py      # Integration tests (in-memory SQLite)
├── docs/
│   ├── ERROR_HANDLING.md        # Error handling documentation
│   └── FAILURE_MODES.md         # Failure modes documentation
├── scripts/
│   └── chaos_test.sh            # Chaos engineering demo script
├── .github/workflows/ci.yml     # CI pipeline
├── Dockerfile                   # Production container
├── docker-compose.yml           # Full stack with restart policies
├── entrypoint.sh                # Docker entrypoint (seed + start)
├── seed.py                      # Idempotent CSV data seeder
├── users.csv                    # MLH seed data — users
├── urls.csv                     # MLH seed data — URLs
├── events.csv                   # MLH seed data — events
├── pyproject.toml               # Dependencies + test config
└── run.py                       # Entry point
```
