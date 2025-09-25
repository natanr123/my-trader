# Database Migration Guide

This guide explains how to create and run database migrations using the Local Alembic → Container Database approach.

## Overview

- **Alembic runs locally** on your machine using `uv`
- **Database runs in Docker container** exposed on port 5432
- **Migration files are created locally** and synced to container via volume mounts
- **Container applies migrations** automatically during startup

## Prerequisites

1. Ensure the database container is running:
   ```bash
   cd /path/to/my-trader
   docker compose up db -d
   ```

2. Ensure local Python environment is set up:
   ```bash
   cd backend
   uv sync  # Install dependencies
   ```

## Creating Migration Files

### 1. Generate a New Migration

From the `backend/` directory:

```bash
# Auto-generate migration based on model changes
uv run alembic revision --autogenerate -m "descriptive message"

# Or create empty migration file
uv run alembic revision -m "descriptive message"
```

**Examples:**
```bash
uv run alembic revision --autogenerate -m "add user profile table"
uv run alembic revision --autogenerate -m "add index to email field"
uv run alembic revision -m "add custom trigger function"
```

### 2. Review Generated Migration

Migration files are created in `backend/app/alembic/versions/`:
```
app/alembic/versions/
├── .keep
└── abc123_descriptive_message.py
```

**Always review the generated migration** before applying:
- Check table/column names are correct
- Verify foreign key relationships
- Ensure data transformations are safe
- Add any custom SQL if needed

### 3. Edit Migration (if needed)

Example migration file structure:
```python
def upgrade():
    # Add your upgrade operations here
    op.create_table('new_table', ...)

def downgrade():
    # Add your downgrade operations here
    op.drop_table('new_table')
```

## Running Migrations

### Automatic (Recommended)

Migrations run automatically when you start the full application:

```bash
cd /path/to/my-trader
docker compose up
```

The `prestart` service will:
1. Wait for database to be healthy
2. Run `alembic upgrade head`
3. Initialize seed data
4. Start the backend service

### Manual Migration

To run migrations manually:

```bash
# From container (recommended for production-like behavior)
docker compose exec backend uv run alembic upgrade head

# From local machine (for development)
cd backend
uv run alembic upgrade head
```

## Common Commands

### Check Migration Status
```bash
# Current revision
uv run alembic current

# Migration history
uv run alembic history --verbose

# Show pending migrations
uv run alembic show head
```

### Rollback Migrations
```bash
# Rollback to previous migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade abc123

# Rollback all migrations
uv run alembic downgrade base
```

### Database Inspection
```bash
# Connect to database
docker compose exec db psql -U postgres -d app

# List tables
docker compose exec db psql -U postgres -d app -c "\dt"

# Check alembic version
docker compose exec db psql -U postgres -d app -c "SELECT * FROM alembic_version;"
```

## Workflow Example

1. **Make model changes** in `app/models/`:
   ```python
   # app/models/models.py
   class User(UserBase, table=True):
       id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
       email: str = Field(unique=True, index=True)
       # Add new field
       phone_number: str | None = Field(default=None)
   ```

2. **Generate migration**:
   ```bash
   cd backend
   uv run alembic revision --autogenerate -m "add phone number to user"
   ```

3. **Review generated file** in `app/alembic/versions/xyz_add_phone_number_to_user.py`

4. **Test the migration**:
   ```bash
   # Apply migration
   uv run alembic upgrade head

   # Check it worked
   docker compose exec db psql -U postgres -d app -c "\d user"
   ```

5. **Start application** (migrations run automatically):
   ```bash
   cd ..
   docker compose up
   ```

## Troubleshooting

### Connection Issues
If Alembic can't connect to the database:
1. Ensure database container is running: `docker compose ps db`
2. Check port 5432 is exposed: `docker compose port db 5432`
3. Verify `.env` settings: `POSTGRES_SERVER=localhost`

### Migration Conflicts
If you get "Target database is not up to date":
1. Check current revision: `uv run alembic current`
2. Check migration history: `uv run alembic history`
3. Reset if needed: `uv run alembic stamp head`

### File Sync Issues
If container doesn't see your migration files:
1. Ensure volume mounts are working: `docker compose config`
2. Restart containers: `docker compose restart`
3. Check file permissions

## Best Practices

1. **Always review auto-generated migrations** before applying
2. **Use descriptive migration messages** that explain the change
3. **Test migrations on sample data** before production
4. **Keep migrations small and focused** - one logical change per migration
5. **Never edit applied migrations** - create a new migration instead
6. **Back up production data** before running migrations
7. **Use transactions** for data migrations when possible

## Environment Variables

Key environment variables for database connection:
```bash
# .env
POSTGRES_SERVER=localhost    # Points to container via port mapping
POSTGRES_PORT=5432          # Exposed port from container
POSTGRES_DB=app            # Database name
POSTGRES_USER=postgres     # Database user
POSTGRES_PASSWORD=changethis # Database password
```

## Architecture

```
Local Development Machine          Docker Container
┌─────────────────────────────┐   ┌─────────────────┐
│                             │   │                 │
│  uv run alembic             │   │                 │
│  ├── reads .env             │   │                 │
│  ├── connects to            │──→│  PostgreSQL     │
│  │   localhost:5432         │   │  :5432          │
│  └── creates migration      │   │                 │
│      files locally          │   │                 │
│                             │   │                 │
│  Volume Mount               │   │                 │
│  backend/app/alembic/ ────────→│  /app/app/      │
│                             │   │  alembic/       │
│                             │   │                 │
│                             │   │  prestart       │
│                             │   │  ├── runs       │
│                             │   │  │   alembic    │
│                             │   │  │   upgrade    │
│                             │   │  └── applies    │
│                             │   │      migrations │
└─────────────────────────────┘   └─────────────────┘
```