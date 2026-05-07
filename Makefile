.PHONY: lint clean debug

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
	find . -type d -name allure-results -exec rm -rf {} +
	find . -type d -name test-results -exec rm -rf {} +
	rm -rf allure-report

report:
	allure generate allure-results -o allure-report --clean
	allure open allure-report
