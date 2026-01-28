# Database Migrations

This directory contains SQL migration scripts for database schema changes.

## Running Migrations

Since there's no migration tool (like Alembic) set up yet, migrations must be run manually:

```bash
# Connect to your PostgreSQL database
psql -U your_user -d your_database -f migrations/001_add_password_reset_fields.sql
```

Or from Python:

```python
from sqlalchemy import text
from src.core.database import engine

with engine.connect() as conn:
    with open("migrations/001_add_password_reset_fields.sql") as f:
        conn.execute(text(f.read()))
    conn.commit()
```

## Future Improvements

Consider setting up Alembic for automatic migration management:

```bash
pip install alembic
alembic init alembic
```
