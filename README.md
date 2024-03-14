# NAVIGATOR DB CLIENT

All things to do with the data model and its storage. Including alembic
migrations and data model code.

## Used by

- [navigator-backend](https://github.com/climatepolicyradar/navigator-backend)
- [navigator-admin-backend](https://github.com/climatepolicyradar/navigator-admin-backend)

## Setting up the repository

To install and run the pre-commit hooks (which run using Trunk.io), please run
`make install_trunk`. This will install and initialise Trunk if it does not
already exist in your PATH. Then, run `make git_hooks` to run Trunk's built-in
linting `trunk check` and formatting `trunk fmt` tools.

Read more about Trunk via their docs page [here](https://docs.trunk.io/).

## How to use as dependency

1. Include the following in the `pyproject.toml`:

```toml
db-client = {git = "https://github.com/climatepolicyradar/navigator-db-client.git", tag = {LATEST_TAG}}
```

2. Run `poetry lock`

## Run migrations

Migrations run automatically at the beginning of the backend service executions
using the `db_client.run_migrations` function.

## Make migrations

```bash
alembic revision --autogenerate --rev-id -m "migration message"
```

## Test

```bash
docker-compose run --rm db_client
```

If you run a test DB out of Dockers:

```bash
source .env
pytest -vvv --cov=db_client --test-alembic --cov-fail-under=95
```

## TODO

- [ ] Create more unit testing here
- [ ] Automatic documentation for pipeline
