# LICENSE HEADER

TOP_DIR=$(shell git rev-parse --show-toplevel)

.PHONY: build
build:
	docker-compose build --no-cache

.PHONY: up
up: install
	docker-compose up -d

.PHONY: down
down:
	docker-compose down

.PHONY: remove
remove: down
	docker-compose run --rm app rm -rf .venv
	docker-compose rm -f

.PHONY: hook
hook:
	ln -sf $(TOP_DIR)/lint .git/hooks/pre-commit

.PHONY: lock
lock:
	docker-compose run --rm app poetry lock

.PHONY: install
install:
	docker-compose run --rm app poetry install --only main

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: tests
tests: remove install
	docker-compose run --rm app poetry run pytest
