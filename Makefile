.PHONY: lint
lint:
	@exec ruff tests --fix
	@exec ruff format tests