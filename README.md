# Crate

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
- **Home** (signed in; the **Crate** title, top left): the homepage, with buttons to the inventory and the overview.
- **Inventory:** three tabs. **Overview**, totals and what needs reordering;
  **Items**, one line per item, with a **New** button, a search box, a low-stock filter and, for admins, **Select**
  to remove several at once (a pop-up asks first); **Movements**, every stock change newest first.
- **Explore** (in the top bar): every public item, newest first, as cards with picture, stock status, quantity, and who added it and when.
  An item whose stock is private is left out.
- **Item profile:** every item has an ID and its own page, laid out like a shop's product page: picture slideshow, stock in and
  out, product details, description and stock history (the history folds away). **Edit** opens a page to change the name, SKU, reorder level,
  description and images, with a separate Privacy section for admins.
- **Profile icon** (right of the top bar): opens **Settings**, and below it **Admin** (admins) and **Log out**.
- **Profile** (in the top bar): your record and the items you added.
- **Settings:** two tabs, **Profile Settings** (rows for name, bio and photo) and **Privacy & Security** (rows for
  password, email and username, and what others can see about you).
- **People:** a person's record shows photo, name, username, role, bio and the items they added, so colleagues can
  recognise them. Open it from a username in the history or, for admins, from **Admin > Users**.
- **Admin** (admins only): two tabs, **Users** (who has an account) and **Staff** (add a staff account). On someone
  else's record an admin also sets their **Permissions** and reads their **Activity log**.

## Rules the app enforces

- Anyone can register. A registered account is always staff. The first admin comes from `.env`.
- Every account has a unique username, which is what other people see. Email addresses are used to sign in
  and are never shown or sent back by the API. You can sign in with the username or the email.
- The first admin's username is `admin`.
- An item can have a description and up to 5 images (PNG, JPEG or WebP, 2 MB each, kept in the database), shown as a
  slideshow. Those allowed to edit items can change them and drag them into order; the first is the main picture.
- A person's record (name, username, role, bio, photo, items added) is visible to anyone signed in.
  Emails never are. Items from before creators were recorded belong to the first admin.
- A staff account can be switched off from adding items, stock in/out, or editing items. Admins can do all of it,
  and cannot change their own role.
- Sign-ins, wrong passwords, stock changes, item changes, account and permission changes are logged per account.
  Only admins read the log. It holds no passwords or email addresses.
- Adding items and recording stock movements need that permission. Only an admin can remove an item; its pictures and
  movements are deleted with it.
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
| `PATCH /api/auth/me`, `POST /api/auth/password`, `POST /api/auth/email`, `GET`, `PUT` and `DELETE /api/auth/photo` | the logged-in user, for themselves |
| `GET /api/users`, `POST /api/users`, `GET /api/users/{id}` | admin |
| `PATCH /api/users/{id}/permissions`, `GET /api/users/{id}/activity` | admin |
| `GET /api/people/{id}`, `.../photo`, `.../items` | logged in |
| `GET /api/movements` (`?limit=`, `?before=`), `GET /api/explore` | logged in |
| `GET /api/items` (`?low=true`), `GET /api/items/{id}`, `GET /api/items/{id}/movements` | logged in |
| `POST /api/items`, `POST /api/items/{id}/movements` | logged in, with that permission |
| `DELETE /api/items/{id}` | admin |
| `PATCH /api/items/{id}` (name, SKU, reorder level, description; `stock_private` and `history_private` admin only), `POST /api/items/{id}/images`, `PUT .../images/order`, `DELETE /api/items/{id}/images/{image}` | logged in, with permission to edit items |
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
