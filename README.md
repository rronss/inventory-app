# Inventory

A small stock-keeping app: log in, see what is in stock, record stock coming in and going out, spot what needs
reordering, and see who is responsible for each item. FastAPI, PostgreSQL and React. Accounts and inventory live in the
database.

## Run it

```bash
cp .env.example .env   # then fill in the four values
docker compose up --build
```

Open http://localhost:8200 and log in with the admin from your `.env`.

## Pages

- **Homepage:** what the app does, with **Sign in** and **Register** tabs on top.
- **Home:** totals, what needs reordering, and how many items are attached to you.
- **Inventory:** two tabs. **Items** to record stock in and out and attach or detach items; **Add an item**.
- **Item profile:** every item has an ID and its own page: stock, who it is attached to and its movement history.
- **My profile:** your attached items, your name, username and password.
- **Users** (admin): see accounts and create staff accounts.

**Sign out** is in the top bar on every page.

## Rules the app enforces

- Anyone can register. A registered account is always staff. The first admin comes from `.env`.
- Every account has a unique username, which is what other people see. Email addresses are used to sign in
  and are never shown or sent back by the API. You can sign in with the username or the email.
- The first admin's username is `admin`.
- Anyone logged in can add an item; it is attached to them. Anyone logged in can record stock movements.
- An unattached item can be claimed by anyone. Only its owner or an admin can detach it; only an admin can assign it
  to someone else.
- Stock never goes below zero, even when two people remove it at the same moment.
- An item is "low" when its quantity is at or below its reorder level.
- Every movement is recorded with who made it.

## API

| Method and path | Who |
|---|---|
| `POST /api/auth/register`, `POST /api/auth/login` | anyone |
| `GET /api/auth/me` | the logged-in user |
| `PATCH /api/auth/me`, `POST /api/auth/password` | the logged-in user, for themselves |
| `GET /api/users`, `POST /api/users` | admin |
| `GET /api/items` (`?low=true`, `?mine=true`), `GET /api/items/{id}`, `GET /api/items/{id}/movements` | logged in |
| `POST /api/items`, `POST /api/items/{id}/movements` | logged in |
| `POST /api/items/{id}/attach`, `POST /api/items/{id}/detach` | logged in, within the rules above |
| `PUT /api/items/{id}/owner` | admin |

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
