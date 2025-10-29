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
db-client @ git+https://github.com/climatepolicyradar/navigator-db-client.git@v{LATEST_TAG}
```

2. Run `uv lock`

## Automated Dependency Updates

When a new release is created in this repository, the GitHub Actions workflow
`update-dependencies.yml` automatically creates pull requests in dependent
repositories to bump the `db-client` version.

### How it works

1. A release is published in `navigator-db-client`
2. The workflow triggers and checks out dependent repositories
3. Updates the `db-client` dependency version in `pyproject.toml`
4. Updates `uv.lock` with the new version
5. Creates a pull request with the changes

### Currently supported repositories

- `[navigator-admin-backend](https://github.com/climatepolicyradar/navigator-admin-backend)`

### TODO dependent repositories

- `[navigator-backend](https://github.com/climatepolicyradar/navigator-backend)`

## Run migrations

Migrations run automatically at the beginning of the backend service executions
using the `db_client.run_migrations` function.

## Make migrations

```bash
# First start postgres
# Ensure you drop and recreate navigator db, so its empty
alembic upgrade head
alembic revision --autogenerate -m "migration message"
```

## Test

DB for test is mocked using `pytest_mock_resources`

```bash
make test
```

## TODO

- [ ] Create more unit testing here
- [ ] Automatic documentation for pipeline
