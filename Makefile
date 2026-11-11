.PHONY: setup lint test up down ci-smoke demo
setup:            ## install the dev environment and git hooks
	uv sync --all-extras
	uv run pre-commit install
lint:             ## ruff + all pre-commit hooks
	uv run pre-commit run --all-files
test:             ## unit tests (no Postgres)
	uv run pytest -m "not integration"
up:               ## local stack: app, scheduler, db, caddy
	docker compose up -d --build
down:
	docker compose down -v
ci-smoke:         ## what the CI docker job runs
	docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --build --wait
	docker compose -f docker-compose.yml -f docker-compose.ci.yml run --rm app screener --help
	docker compose -f docker-compose.yml -f docker-compose.ci.yml down -v
demo:             ## demo stack with the 100k-account subsample preloaded (TRA-14)
	docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --build --wait
