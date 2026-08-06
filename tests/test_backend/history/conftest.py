import pytest

# ── Rate-limit: skip remaining history tests on 429 ─────────────────────────

_rate_limited = False
_rate_limit_retry_after = None


def _rate_limit_message():
    msg = "429 — рейт-лимит API исчерпан, history-тесты пропущены"
    if _rate_limit_retry_after:
        msg += f". Повторить после {_rate_limit_retry_after}"
    return msg


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    global _rate_limited, _rate_limit_retry_after
    outcome = yield
    report = outcome.get_result()
    if report.failed and "429" in str(report.longrepr):
        _rate_limited = True
        if _rate_limit_retry_after is None:
            from datetime import datetime, timedelta
            retry_time = datetime.now() + timedelta(hours=1)
            _rate_limit_retry_after = retry_time.strftime("%H:%M")
        report.longrepr = str(report.longrepr) + f"\n\n>>> {_rate_limit_message()}"


@pytest.fixture(autouse=True)
def _skip_if_rate_limited():
    if _rate_limited:
        pytest.skip(_rate_limit_message())
