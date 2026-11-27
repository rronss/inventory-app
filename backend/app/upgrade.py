"""Adds columns that appeared after a database was first created. A larger app would use Alembic."""
from sqlalchemy import inspect, text

COLUMNS = {
    "users": {
        "name": "VARCHAR(80) NOT NULL DEFAULT ''",
        "username": "VARCHAR(30) NOT NULL DEFAULT ''",
        "bio": "VARCHAR(500) NOT NULL DEFAULT ''",
        "photo_version": "INTEGER NOT NULL DEFAULT 0",
        "can_add_items": "BOOLEAN NOT NULL DEFAULT TRUE",
        "can_move_stock": "BOOLEAN NOT NULL DEFAULT TRUE",
        "can_edit_items": "BOOLEAN NOT NULL DEFAULT TRUE",
        "chat_from": "VARCHAR(10) NOT NULL DEFAULT 'everyone'",
    },
    "items": {
        "description": "VARCHAR(1000) NOT NULL DEFAULT ''",
        "stock_private": "BOOLEAN NOT NULL DEFAULT FALSE",
        "history_private": "BOOLEAN NOT NULL DEFAULT FALSE",
        "creator_id": "INTEGER REFERENCES users(id)",
        "created_at": "TIMESTAMP WITH TIME ZONE",  # unknown for what is already there
    },
    # all 0 at first, so pictures stay in the order they were added
    "item_images": {"position": "INTEGER NOT NULL DEFAULT 0"},
}


def add_missing_columns(engine) -> list[str]:
    added = []
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in COLUMNS.items():
            if not inspector.has_table(table):
                continue  # create_all makes new tables, with all their columns
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
                    added.append(f"{table}.{name}")
        # Items from before creators were recorded are given to the first admin.
        if "items.creator_id" in added:
            first_admin = "(SELECT id FROM users WHERE role = 'admin' ORDER BY id LIMIT 1)"
            connection.execute(text(f"UPDATE items SET creator_id = {first_admin}"))
        # Accounts from before usernames get a placeholder, which their owner can change.
        connection.execute(text("UPDATE users SET username = 'user' || id WHERE username = ''"))
        # create_all does not add indexes to a table that already exists. Same name as in models.py.
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username_lower ON users (lower(username))"))
    return added
