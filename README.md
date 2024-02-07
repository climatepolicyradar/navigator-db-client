# NAVIGATOR DB CLIENT
All things to do with the datamodel and its storage. Including alembic migrations and datamodel code.

## Used by
- [navigator-backend](https://github.com/climatepolicyradar/navigator-backend)
- [navigator-admin-backend](https://github.com/climatepolicyradar/navigator-admin-backend)

> ⚠️ Dockerfile should indicate where the DB client is installed inside of Docker containers (maybe there is a better way to do this).

## Installation

1. Include the following in the `pyproject.toml`:

```
db-client = {git = "https://github.com/climatepolicyradar/navigator-db-client.git", tag = {LATEST_TAG}}
```

2. Run `poetry lock`

## Run migrations
Migrations run automatically at the begginig of the backend service executions using the `db_client.run_migrations` function.

## Make migrations
TODO

## Test
TODO
(best deal: run test for every backend in this CI repository...)