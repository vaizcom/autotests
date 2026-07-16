import pytest

# ── Rate-limit: skip remaining history tests on 429 ─────────────────────────

RATE_LIMIT_HINT = (
    "\n\n>>> 429 Too Many Requests — рейт-лимит API исчерпан.\n"
    ">>> Оставшиеся history-тесты будут пропущены.\n"
    ">>> Подождите ~1 час и запустите повторно."
)

_rate_limited = False


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    global _rate_limited
    outcome = yield
    report = outcome.get_result()
    if report.failed and "429" in str(report.longrepr):
        _rate_limited = True
        report.longrepr = str(report.longrepr) + RATE_LIMIT_HINT


@pytest.fixture(autouse=True)
def _skip_if_rate_limited():
    if _rate_limited:
        pytest.skip("429 — рейт-лимит API исчерпан, history-тесты пропущены")
