.PHONY: lint
lint:
	@exec ruff tests --fix
	@exec ruff format tests

clear:
	find . -type d -name allure-results -exec rm -rf {} \;

report:
	allure generate allure-results -o allure-report --clean
	allure open allure-report
