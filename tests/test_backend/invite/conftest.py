import pytest


RATE_LIMIT_HINT = (
    "\n\n>>> 429 Too Many Requests — превышен лимит инвайтов (20/час на пользователя).\n"
    ">>> При повторном прогоне в течение часа это ожидаемое поведение.\n"
    ">>> Подождите ~1 час или используйте другого пользователя."
)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed and "429" in str(report.longrepr):
        report.longrepr = str(report.longrepr) + RATE_LIMIT_HINT
