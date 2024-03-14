.PHONEY: test git_hooks

git_hooks:
	poetry run pre-commit install --install-hooks

test:
	pytest -vvv --cov=db_client --cov-fail-under=80
