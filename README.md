# Crate

A small stock-keeping app: log in, see what is in stock, record stock coming in and going out, spot what needs
reordering, and keep a page for each item. FastAPI, PostgreSQL and React. Accounts and inventory live in the
database; picture files can live in S3 instead.

## Run it

There are two Compose files: `docker-compose.yml` for **development** (builds the source, runs its own database) and
`docker-compose.prod.yml` for **production** (published images, HTTPS, RDS and S3; see [Deploy](#deploy)).

```bash
cp .env.example .env   # then fill in the four values
docker compose up --build
```

Open http://localhost:8200 and log in with the admin from your `.env`.

## Pages

- **Homepage:** what the app does, with **Sign in** and **Register** tabs on top.
- **Home** (signed in; the **Crate** title, top left): the homepage, with buttons to the inventory and the overview.
- **Inventory:** three tabs. **Items**, one line per item, with a **New** button, a search box, a low-stock filter
  and, for admins, **Select** to remove several at once (a pop-up asks first); **Movements**, every stock change newest first;
  **Overview**, totals and what needs reordering.
- **Inbox** (in the top bar, with the number unread): three tabs. **Chats** (with a search bar and the total; **New** opens a form for the user and the first message) between two people, which nobody else can
  read in the app. **Alerts**: tells you when an item you added runs low or out, when someone else
  changes its stock, edits or removes it, and when your permissions change. Private information is never included.
- **Inbox > Updates:** notes about the app (written in `backend/app/updates.py`) and messages admins post to everyone.
- **Friends** (in the account menu): **Add friend** (by username), search people and add them; each friend has a **Chat** button; **Edit** ticks friends to
  **Unfriend** or **Block**. Blocking ends the friendship and stops
  requests and messages both ways; the other person is not told, and shared inventory stays visible.
- **Friend requests:** send one from an item's card, a person's record or **Friends** (by username); accept or
  decline it on **Friends** or in **Alerts**. Being friends shows nothing that was hidden.
- **Explore** (in the top bar): a search bar, a filter list at the top right (**Recents**, newest first, the default;
  **All items**, A to Z; **Only friends**; **My items**) and every public item, newest first, as cards with picture, stock status, quantity, and who added it and when.
  An item whose stock is private is left out.
- **Item profile:** every item has an ID and its own page, laid out like a shop's product page: picture slideshow, stock in and
  out, product details, description and stock history (the history folds away). **Edit** opens a page to change the name, SKU, reorder level,
  description and images, with a separate Privacy section for admins.
- **Profile icon** (right of the top bar): opens **Profile**, **Friends** and **Settings**, and below them **Admin** (admins) and
  **Log out**.
- **Profile:** your record and the items you added, as picture cards.
- **Who can chat me** (Settings > Privacy & Security): **Everyone**, the default, or **Friends only**. With
  **Friends only**, others are told so when they try; you can still write to them, but they cannot reply.
- **Settings:** two tabs, **Profile Settings** (rows for bio and photo; the photo is one of five default
  avatars or your own upload) and **Privacy & Security** (rows for
  password, email and username, and what others can see about you).
- **Profile menu** (three lines, top right of every profile): on yours, Edit profile, Friends and Privacy; on someone
  else's, Chat, the friend options and Block.
- **People:** a person's record shows user ID, photo, username, role, bio, number of friends and the items they added, so colleagues can
  recognise them. Open it from a username in the history or, for admins, from **Admin > Users**.
- **Admin** (admins only): two tabs, **Users** (who has an account) and **Staff** (add a staff account). On someone
  else's record an admin also sets their **Permissions** and reads their **Activity log**.

## Rules the app enforces

- Anyone can register. A registered account is always staff, and can change stock and edit only the items it added;
  an admin can lift that under **Permissions**. The first admin comes from `.env`.
- After 5 wrong passwords for an account (20 from one address) sign-in waits 15 minutes. One address can register 10
  times an hour. With Cloudflare Turnstile keys set, registering also needs a robot check.
- Every account has a unique username, which is what other people see. Email addresses are used to sign in
  and are never shown or sent back by the API. You can sign in with the username or the email.
- The first admin's username is `admin`.
- An item can have a description and up to 5 images (PNG, JPEG or WebP, 2 MB each), shown as a
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
| `GET /api/auth/config`, `POST /api/auth/register`, `POST /api/auth/login` | anyone |
| `GET /api/auth/me` | the logged-in user |
| `PATCH /api/auth/me`, `POST /api/auth/password`, `POST /api/auth/email`, `GET`, `PUT` and `DELETE /api/auth/photo` | the logged-in user, for themselves |
| `GET /api/users`, `POST /api/users`, `GET /api/users/{id}` | admin |
| `PATCH /api/users/{id}/permissions`, `GET /api/users/{id}/activity` | admin |
| `GET /api/people`, `GET /api/people/{id}`, `.../photo`, `.../items` | logged in |
| `GET /api/messages`, `GET` and `POST /api/messages/{person}`, `POST .../read` | logged in, own conversations only |
| `GET /api/updates`, `POST /api/updates/read` | logged in |
| `POST /api/updates`, `DELETE /api/updates/{id}` | admin |
| `GET /api/friends`, `GET`, `POST` and `DELETE /api/friends/{person}`, `POST .../accept`, `PUT` and `DELETE .../block` | logged in, own friends only |
| `GET /api/movements` (`?limit=`, `?before=`), `GET /api/explore` | logged in |
| `GET /api/inbox`, `.../unread`, `POST /api/inbox/read`, `POST /api/inbox/{id}/read` | logged in, own alerts only |
| `GET /api/items` (`?low=true`), `GET /api/items/{id}`, `GET /api/items/{id}/movements` | logged in |
| `POST /api/items`, `POST /api/items/{id}/movements` | logged in, with that permission |
| `DELETE /api/items/{id}` | admin |
| `PATCH /api/items/{id}` (name, SKU, reorder level, description; `stock_private` and `history_private` admin only), `POST /api/items/{id}/images`, `PUT .../images/order`, `DELETE /api/items/{id}/images/{image}` | logged in, with permission to edit items |
| `GET /api/items/{id}/images/{image}` | logged in |

## Where pictures are kept

Item pictures and profile photos are kept in the database unless you set:

```bash
PICTURE_STORAGE=s3
PICTURE_BUCKET=your-private-bucket
```

The backend then writes the files to that bucket and passes them through to signed-in users, so the bucket needs no
public access. It needs permission to get, put and delete objects in it (on EC2, through the server's role; no keys
in `.env`). Pictures saved before the switch stay in the database and are still shown.

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

## Deploy

[infrastructure/](infrastructure/README.md) holds Terraform (AWS resources) and Ansible (server setup and
deployment).

## CI

`ci` lints and tests the backend and builds the frontend, on pushes to `main` and `change/**` and on pull requests.
When it fails, `triage` asks [ci-triage-agent](https://github.com/rronss/ci-triage-agent) to diagnose the run and post
the result to Slack. It needs two repository secrets, `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL`.

`images` publishes the backend and frontend containers to GitHub's registry after `ci` passes on `main`.
