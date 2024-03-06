.PHONEY: test git_hooks

git_hooks:
	poetry run pre-commit install --install-hooks

test:
	docker-compose build
	docker-compose run --rm db_client
