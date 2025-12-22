.PHONEY: test git_hooks install_trunk uninstall_trunk

install_trunk:
	$(eval trunk_installed=$(shell trunk --version > /dev/null 2>&1 ; echo $$? ))
ifneq (${trunk_installed},0)
	$(eval OS_NAME=$(shell uname -s | tr A-Z a-z))
	curl https://get.trunk.io -fsSL | bash
endif

uninstall_trunk:
	sudo rm -if `which trunk`
	rm -ifr ${HOME}/.cache/trunk

configure_pyright:
	trunk actions run configure-pyright

setup_with_pyenv: install_trunk ## Sets up a local dev environment using Pyenv
	$(eval venv_name=$(shell  grep 'venv =' pyproject.toml | cut -d '"' -f 2 ))
	if [ -n "$(venv_name)" ] && ! pyenv versions --bare | grep -q "^$(venv_name)$$"; then \
		$(eval python_version=$(shell grep 'python =' pyproject.toml | cut -d '"' -f 2 | sed 's/^\^//')) \
		$(eval pyenv_version=$(shell pyenv versions --bare | grep$(python_version) )) \
		pyenv virtualenv $(pyenv_version) $(venv_name); \
	fi
	@eval "$$(pyenv init -)" && \
	pyenv activate $(venv_name) && \
	poetry install

	make configure_pyright

check:
	trunk fmt
	trunk check

test:
	poetry run pytest -vvv --cov=db_client --cov-fail-under=80 --cov-report=term --cov-report=html

update-python-version:
	poetry python install $(head -n1 .python-version)
