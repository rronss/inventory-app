"""Adds columns that appeared after a database was first created. A larger app would use Alembic."""
from sqlalchemy import inspect, text

COLUMNS = {
    "users": {"name": "VARCHAR(80) NOT NULL DEFAULT ''", "username": "VARCHAR(30) NOT NULL DEFAULT ''"},
    "items": {"owner_id": "INTEGER REFERENCES users(id)"},
}


def add_missing_columns(engine) -> list[str]:
    added = []
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in COLUMNS.items():
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
                    added.append(f"{table}.{name}")
        # Accounts from before usernames get a placeholder, which their owner can change.
        connection.execute(text("UPDATE users SET username = 'user' || id WHERE username = ''"))
        # create_all does not add indexes to a table that already exists. Same name as in models.py.
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username_lower ON users (lower(username))"))
    return added
