.PHONY: lint
lint:
	@exec ruff check core tests --fix
	@exec ruff format core tests