.PHONY: lint lint-frontend lint-backend clean debug report

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
	@TS=$$(python3 -c "from datetime import datetime; m=['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']; n=datetime.now(); print(f'{n.day} {m[n.month-1]}, {n.strftime(\"%H:%M:%S\")}')"); \
	echo "⏱  TS=$$TS"; \
	echo "📋 test_01 → $(TEST) → test_99"; \
	TEST_TS=$$TS pytest -k "test_01 or $(TEST) or test_99" $(FILE)

lint:
	@exec ruff tests --fix
	@exec ruff format tests

lint-frontend:
	@exec ruff tests/test_frontend --fix
	@exec ruff format tests/test_frontend

lint-backend:
	@exec ruff tests/test_backend --fix
	@exec ruff format tests/test_backend

clean:
	find . -type d -name "allure-results*" -exec rm -rf {} + 2>/dev/null; true
	rm -rf allure-report
	find . -type d -name test-results -exec rm -rf {} + 2>/dev/null; true

report:
	@RESULTS=$$(find . -type d -name "allure-results*" -not -empty 2>/dev/null | head -1); \
	if [ -z "$$RESULTS" ]; then \
		echo "No allure results found. Run tests first."; exit 1; \
	fi; \
	echo "Using: $$RESULTS"; \
	allure generate $$RESULTS -o allure-report --clean
	allure open allure-report
