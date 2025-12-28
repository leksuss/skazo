.PHONY: lint format

lint:
	uv run --group dev ruff format --check .
	uv run --group dev ruff check .

format:
	uv run --group dev ruff format .
	uv run --group dev ruff check --fix .
