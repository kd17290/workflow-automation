# LICENSE HEADER

TOP_DIR=$(shell git rev-parse --show-toplevel)

.PHONY: build
build:
	docker-compose build

.PHONY: up
up:
	docker-compose up -d

.PHONY: down
down:
	docker-compose down

.PHONY: remove
remove: down
	docker-compose rm -f

.PHONY: tests
tests: down
	docker-compose run --rm app pytest tests
	rm -rf data

.PHONY: hook
hook:
	ln -sf $(TOP_DIR)/lint .git/hooks/pre-commit

.PHONY: lock
lock:
	poetry lock --no-update

.PHONY: install
install:
	poetry install --only main

.PHONY: lint
lint:
	pre-commit run --all-files
