# Error Handling Documentation

This document describes how the URL Shortener service handles errors, as required for the **Silver Tier** of the Reliability Engineering Quest.

## Response Format

All error responses are returned as **JSON** — never raw HTML or Python stack traces. This ensures clients can always parse the error programmatically.

```json
{
  "error": "Error Type",
  "message": "Human-readable explanation"
}
```

---

## HTTP Error Codes

### 400 Bad Request

Returned when the client sends invalid data.

| Scenario | Response Body |
|---|---|
| Missing `url` field in POST body | `{"error": "Missing 'url' field in request body"}` |
| `url` is not a string | `{"error": "URL must be a non-empty string"}` |
| `url` is empty or whitespace | `{"error": "URL must be a non-empty string"}` |
| `url` is not HTTP/HTTPS | `{"error": "Invalid URL. Must be a valid HTTP or HTTPS URL", "example": "https://example.com"}` |
| Invalid short code format (non-alphanumeric) | `{"error": "Invalid short code format"}` |

**Example:**
```bash
curl -X POST http://localhost:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "not-a-real-url"}'
```
```json
HTTP/1.1 400 Bad Request
{
  "error": "Invalid URL. Must be a valid HTTP or HTTPS URL",
  "example": "https://example.com"
}
```

---

### 404 Not Found

Returned when the requested resource does not exist.

| Scenario | Response Body |
|---|---|
| Short code not in database | `{"error": "Short URL not found", "short_code": "<code>"}` |
| Route does not exist | `{"error": "Not Found", "message": "The requested resource does not exist."}` |

**Example:**
```bash
curl http://localhost:5000/abc123
```
```json
HTTP/1.1 404 Not Found
{
  "error": "Short URL not found",
  "short_code": "abc123"
}
```

---

### 405 Method Not Allowed

Returned when an unsupported HTTP method is used on an endpoint.

| Scenario | Response Body |
|---|---|
| POST to `/health` | `{"error": "Method Not Allowed", "message": "..."}` |
| GET to `/shorten` | `{"error": "Method Not Allowed", "message": "..."}` |

---

### 500 Internal Server Error

Returned for unexpected server-side failures (e.g., database connectivity issues after all retries).

```json
HTTP/1.1 500 Internal Server Error
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred. Please try again later."
}
```

> **Note:** The application never exposes Python stack traces to the client. All 500 errors are caught by the global error handler and returned as clean JSON.

---

## Design Principles

1. **Always JSON**: No HTML error pages. All error responses are `application/json`.
2. **Descriptive messages**: Error messages guide the client on what went wrong.
3. **No stack traces exposed**: Internal errors are logged server-side but sanitized before returning to the client.
4. **Graceful degradation**: Even under failure, the API contract is maintained.
