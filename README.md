# Inventory

A small stock-keeping app: sign in, see what is in stock, record stock coming in and going out, and spot what needs
reordering. FastAPI, PostgreSQL and React.

## Run it

```bash
cp .env.example .env   # then fill in the four values
docker compose up --build
```

Open http://localhost:8200 and sign in with the admin from your `.env`.

## Rules the app enforces

- There is no public sign-up. The first admin comes from `.env`; admins create staff accounts.
- Admins add items. Admins and staff record stock movements.
- Stock never goes below zero, even when two people remove it at the same moment.
- An item is "low" when its quantity is at or below its reorder level.
- Every movement is recorded with who made it.

## API

| Method and path | Who |
|---|---|
| `POST /api/auth/login`, `GET /api/auth/me` | anyone with an account |
| `POST /api/users` | admin |
| `GET /api/items` (`?low=true`), `GET /api/items/{id}/movements` | signed in |
| `POST /api/items` | admin |
| `POST /api/items/{id}/movements` | signed in |

## Develop

```bash
cd backend && pip install -r requirements-dev.txt && ruff check . && pytest
```

```bash
cd frontend && npm ci && npm run dev
```

The dev server runs on http://localhost:5180 and forwards `/api` to a backend on port 8100:

```bash
cd backend && SECRET_KEY=$(openssl rand -hex 32) ADMIN_EMAIL=you@example.com ADMIN_PASSWORD=choose-one uvicorn app.main:app --port 8100
```

## CI

`ci` lints and tests the backend and builds the frontend, on pushes to `main` and `change/**` and on pull requests.
When it fails, `triage` asks [ci-triage-agent](https://github.com/rronss/ci-triage-agent) to diagnose the run and post
the result to Slack. It needs two repository secrets, `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL`.
