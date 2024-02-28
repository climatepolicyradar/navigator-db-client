.PHONEY: test

test:
	docker-compose run --rm db_client
