.PHONY: lint clean debug report report-backend report-frontend

# Отладка отдельного теста с автоматическим сетапом и клинапом.
# Генерирует TS, запускает test_01 → целевой тест → test_99 в одном прогоне.
#
# Использование:
#   make debug FILE=tests/test_frontend/tests/tasks/test_task_fields.py TEST=test_12
#   make debug FILE=tests/test_frontend/tests/milestones/test_milestone_fields.py TEST=test_07
#
# Для тестов с доп. сетапом (подзадачи):
#   make debug FILE=tests/.../test_task_fields.py TEST="test_11 or test_12"
debug:
	@TS=$$(date +%H%M%S); \
	echo "⏱  TS=$$TS"; \
	echo "📋 test_01 → $(TEST) → test_99"; \
	TEST_TS=$$TS pytest -k "test_01 or $(TEST) or test_99" $(FILE)

lint:
	@exec ruff tests --fix
	@exec ruff format tests

clean:
	rm -rf allure-results allure-results-backend allure-results-frontend
	rm -rf allure-report allure-report-backend allure-report-frontend
	find . -type d -name test-results -exec rm -rf {} +

report-backend:
	allure generate allure-results-backend -o allure-report-backend --clean
	allure open allure-report-backend

report-frontend:
	allure generate allure-results-frontend -o allure-report-frontend --clean
	allure open allure-report-frontend

report:
	@if [ -d allure-results-frontend ]; then \
		allure generate allure-results-frontend -o allure-report-frontend --clean; \
		allure open allure-report-frontend; \
	elif [ -d allure-results-backend ]; then \
		allure generate allure-results-backend -o allure-report-backend --clean; \
		allure open allure-report-backend; \
	else \
		echo "No allure results found. Run tests first."; \
	fi
