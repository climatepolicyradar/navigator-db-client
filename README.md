# NAVIGATOR DB CLIENT
All things to do with the datamodel and its storage. Including alembic migrations and datamodel code.

## Used by
- [navigator-backend](https://github.com/climatepolicyradar/navigator-backend)
- [navigator-admin-backend](https://github.com/climatepolicyradar/navigator-admin-backend)

## Installation

1. Include the following in the `pyproject.toml`:

```
db-client = {git = "https://github.com/climatepolicyradar/navigator-db-client.git", tag = {LATEST_TAG}}
```

2. Run `poetry lock`

## Run migrations
Migrations run automatically at the begginig of the backend service executions using the `db_client.run_migrations` function.

## Make migrations

```bash
alembic revision --autogenerate --rev-id -m "migration message"
```

## Test

```bash
pytest -vvv --cov=db_client --test-alembic --cov-fail-under=95
```

## TODO:

[x] Pass the alembic files path in a better way
[ ] Create some unit testing here
[x] Move schema tests
[ ] Include in the admin backend the migrations run
[ ] Automatic documentation?

## CAUTION
- test_db_url hardcoeded for tests in `conftest`
