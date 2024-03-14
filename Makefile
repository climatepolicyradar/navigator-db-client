.PHONEY: test git_hooks

install_trunk:
	$(eval trunk_installed=$(shell trunk --version > /dev/null 2>&1 ; echo $$? ))
ifneq (${trunk_installed},0)
	$(eval OS_NAME=$(shell uname -s | tr A-Z a-z))
	curl https://get.trunk.io -fsSL | bash
endif

git_hooks:
	trunk fmt
	trunk check

test:
	poetry run pytest -vvv --cov=db_client --cov-fail-under=80
