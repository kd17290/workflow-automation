# LICENSE HEADER

TOP_DIR=$(shell git rev-parse --show-toplevel)

.PHONY: build
build:
	docker-compose build workflow --no-cache

.PHONY: up
up: install
	docker-compose up -d workflow

.PHONY: down
down:
	docker-compose down workflow workflow_db

.PHONY: remove
remove: down
	docker-compose run --rm workflow rm -rf .venv
	docker-compose rm -f

.PHONY: hook
hook:
	ln -sf $(TOP_DIR)/lint .git/hooks/pre-commit

.PHONY: lock
lock:
	docker-compose run --rm workflow poetry lock

.PHONY: install
install:
	# Bring up the database service to ensure it is postgres
	docker-compose run --rm workflow poetry install --only main

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: tests
tests: remove install
	docker-compose run --rm workflow poetry run pytest
