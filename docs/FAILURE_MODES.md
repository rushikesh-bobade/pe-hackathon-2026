# Failure Modes Documentation

This document describes the known failure modes of the URL Shortener service, their symptoms, and how the system responds — as required for the **Gold Tier** of the Reliability Engineering Quest.

---

## Failure Mode 1: Application Process Crash

**What happens:** The Flask/Gunicorn process exits unexpectedly (OOM, unhandled exception, SIGKILL).

**Symptoms:**
- HTTP connections refused on port 5000
- `/health` endpoint returns no response

**System Response:**
- Docker's `restart: always` policy automatically restarts the container within seconds.
- No manual intervention required.

**Demo command:**
```bash
# Kill the running container — watch it restart automatically
docker kill url-shortener
docker ps  # Container appears again within seconds
```

**Recovery Time:** ~5–10 seconds (container restart + app boot)

---

## Failure Mode 2: Database Connection Lost

**What happens:** The PostgreSQL container crashes or the network link is severed.

**Symptoms:**
- `POST /shorten` and `GET /<code>` return errors
- `/health` still returns `200 OK` (health check does not query DB intentionally — it indicates the app process is alive)

**System Response:**
- The `db` service also has `restart: always`, so the database comes back automatically.
- The app re-establishes its connection pool on the next request via Peewee's `reuse_if_open=True` hook.
- Requests during the outage window receive a `500 Internal Server Error` with a clean JSON response (no stack trace).

**Recovery Time:** ~10–20 seconds (DB boot + connection re-establishment)

---

## Failure Mode 3: Invalid or Malformed Input

**What happens:** A client sends garbage data — missing fields, non-URL strings, wrong types.

**Symptoms:**
- Client receives a 4xx error

**System Response:**
- The request is validated **before** touching the database.
- A `400 Bad Request` JSON response is returned immediately.
- The application does **not** crash.
- No side effects occur (no partial DB writes).

**Example:**
```bash
curl -X POST http://localhost:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "javascript:alert(1)"}'
# → HTTP 400: {"error": "Invalid URL. Must be a valid HTTP or HTTPS URL", ...}
```

---

## Failure Mode 4: Short Code Collision

**What happens:** The random 6-character code generator produces a code already in the database.

**Symptoms (without mitigation):** Database `IntegrityError` on unique constraint.

**System Response:**
- The route handler retries up to **5 times** with a new random code.
- The probability of 5 consecutive collisions is astronomically low (~1 in 56 billion).
- If all retries fail, a `500` error is returned with a clear message.

---

## Failure Mode 5: Unknown Route Accessed

**What happens:** A client navigates to a route that does not exist.

**System Response:**
- Flask's global `404` handler intercepts the request.
- Returns clean JSON: `{"error": "Not Found", "message": "..."}`
- No stack trace. No HTML error page.

---

## Failure Mode 6: Out-of-Memory (OOM)

**What happens:** The container is killed by the OS due to excessive memory use.

**System Response:**
- Docker's `restart: always` restarts the container.
- Gunicorn's pre-fork worker model means other workers continue serving while one is recycled.

---

## Summary Table

| Failure Mode | Detected By | Auto-Recovered? | Client Sees |
|---|---|---|---|
| App process crash | Docker health check | ✅ Yes (restart: always) | Brief connection refused |
| Database crash | App exception | ✅ Yes (restart: always) | `500 Internal Server Error` (JSON) |
| Invalid input | Request validation | N/A — not a real failure | `400 Bad Request` (JSON) |
| Short code collision | DB IntegrityError | ✅ Yes (retry loop) | Transparent — user gets a code |
| Unknown route | Flask 404 handler | N/A | `404 Not Found` (JSON) |
| OOM kill | Docker | ✅ Yes (restart: always) | Brief connection refused |
