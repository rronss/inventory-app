# Inventory

A small stock-keeping app: log in, see what is in stock, record stock coming in and going out, spot what needs
reordering, and keep a page for each item. FastAPI, PostgreSQL and React. Accounts and inventory live in the
database.

## Run it

```bash
cp .env.example .env   # then fill in the four values
docker compose up --build
```

Open http://localhost:8200 and log in with the admin from your `.env`.

## Pages

- **Homepage:** what the app does, with **Sign in** and **Register** tabs on top.
- **Home:** totals and what needs reordering.
- **Inventory:** three tabs. **Items**, one line per item; **Movements**, every stock change newest first; **Add an item**.
- **Item profile:** every item has an ID and its own page, laid out like a shop's product page: picture slideshow, stock in and
  out, product details, description and stock history (the history folds away). **Edit** opens a page to change the name, SKU, reorder level,
  description and images, with a separate Privacy section for admins.
- **My profile:** your name, username and password.
- **Users** (admin): see accounts and create staff accounts.

**Sign out** is in the top bar on every page.

## Rules the app enforces

- Anyone can register. A registered account is always staff. The first admin comes from `.env`.
- Every account has a unique username, which is what other people see. Email addresses are used to sign in
  and are never shown or sent back by the API. You can sign in with the username or the email.
- The first admin's username is `admin`.
- An item can have a description and up to 5 images (PNG, JPEG or WebP, 2 MB each, kept in the database), shown as a
  slideshow. Anyone logged in can change them.
- Anyone logged in can add an item and record stock movements.
- An admin can make two things private per item, separately. **Stock** (quantity, status, reorder level): other users
  get none of it from any endpoint and cannot move that item's stock. **Stock history**: other users cannot read its
  movements. SKU, ID and description are always visible to a signed-in user.
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
| `GET /api/movements` (`?limit=`, `?before=`) | logged in |
| `GET /api/items` (`?low=true`), `GET /api/items/{id}`, `GET /api/items/{id}/movements` | logged in |
| `POST /api/items`, `POST /api/items/{id}/movements` | logged in |
| `PATCH /api/items/{id}` (name, SKU, reorder level, description; `stock_private` and `history_private` admin only), `POST /api/items/{id}/images`, `DELETE /api/items/{id}/images/{image}` | logged in |
| `GET /api/items/{id}/images/{image}` | logged in |

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

## Sample data

Three sample items with descriptions and pictures, loaded into a running app:

```bash
set -a && . ./.env && set +a && python3 sample-data/load.py
```

The pictures are drawn by `sample-data/draw.py` (needs Pillow).

## CI

`ci` lints and tests the backend and builds the frontend, on pushes to `main` and `change/**` and on pull requests.
When it fails, `triage` asks [ci-triage-agent](https://github.com/rronss/ci-triage-agent) to diagnose the run and post
the result to Slack. It needs two repository secrets, `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL`.
