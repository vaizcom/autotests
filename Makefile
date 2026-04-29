.PHONY: lint clean
lint:
	@exec ruff tests --fix
	@exec ruff format tests

clean:
	find . -type d -name allure-results -exec rm -rf {} +
	find . -type d -name test-results -exec rm -rf {} +
	rm -rf allure-report

report:
	allure generate allure-results -o allure-report --clean
	allure open allure-report
