import pytest

from tests.test_frontend.core.settings import BASE_URL, FRONTEND_EMAIL, FRONTEND_PASSWORD


@pytest.fixture(scope="session")
def auth_state(playwright):
    """Логинится один раз на сессию и сохраняет состояние браузера."""
    browser = playwright.chromium.launch()
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto(f"{BASE_URL}/auth/sign-in")
    page.get_by_role("textbox", name="Email").fill(FRONTEND_EMAIL)
    page.get_by_role("textbox", name="Password").fill(FRONTEND_PASSWORD)
    page.get_by_role("button", name="Continue with Email").click()
    page.wait_for_load_state("networkidle")
    state = context.storage_state()
    context.close()
    browser.close()
    return state


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, auth_state):
    """Все тесты стартуют уже залогиненными."""
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "storage_state": auth_state,
    }
