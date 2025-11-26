# Smoke test script

This directory contains a small script `smoke_test.py` that performs a basic smoke test for the `auth` and `data` services.

What it does
- Requests an OAuth token from the Auth service (`/token`) using client_credentials
- Submits a simple SQL statement to the Data service (`/api/v1/statements`)
- Polls the statement status endpoint and then cancels the statement

Running
```bash
# Run with environment vars (defaults shown):
AUTH_URL=http://localhost:8081 DATA_URL=http://localhost:8000 \
  CLIENT_ID=m2m-client CLIENT_SECRET=secret123 ./scripts/smoke_test.py

# Or use provided flags:
./scripts/smoke_test.py --auth-url http://localhost:8081 --data-url http://localhost:8000 \
  --client-id m2m-client --client-secret secret123
```

Environment variables
- AUTH_URL: Auth service base URL (default: http://localhost:8081)
- DATA_URL: Data API base URL (default: http://localhost:8000)
- CLIENT_ID / CLIENT_SECRET: Client credentials for the client_credentials grant (default: m2m-client / secret123)
- KEY_DATE / SCOPE: Optional values passed to the token endpoint

Notes
- The Data service expects a working Firestore instance; some endpoints may return 504 if Firestore is not configured in your environment.
- This is a basic smoke test and not intended for load testing or detailed validation.
