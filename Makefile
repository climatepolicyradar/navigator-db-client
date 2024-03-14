.PHONEY: test git_hooks

install_trunk:
	$(eval trunk_installed=$(shell trunk --version > /dev/null 2>&1 ; echo $$? ))
ifneq ($(trunk_installed),0)
	$(eval OS_NAME=$(shell uname -s | tr A-Z a-z))
ifeq ($(OS_NAME),linux)
	curl https://get.trunk.io -fsSL | bash
endif
ifeq ($(OS_NAME),darwin)
	brew install trunk-io
endif
endif

git_hooks: install_trunk
	trunk fmt
	trunk check

test:
	pytest -vvv --cov=db_client --cov-fail-under=80
