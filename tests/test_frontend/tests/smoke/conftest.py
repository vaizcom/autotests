import time

import pytest

from tests.test_frontend.tests.auth.conftest import sign_up_new_account


@pytest.fixture(scope='session')
def smoke_auth_state(playwright, _configure_test_id):
    """Регистрирует новый аккаунт и сохраняет сессию для smoke-тестов."""
    ts = int(time.time())
    email = f'TST_smoke_{ts}@mailinator.com'

    browser = playwright.chromium.launch()
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    try:
        sign_up_new_account(page, email)
    except Exception as e:
        context.close()
        browser.close()
        pytest.skip(f'Sign-up не прошёл: {str(e).split(chr(10))[0]}')

    state = context.storage_state()
    context.close()
    browser.close()
    return state


@pytest.fixture(scope='session')
def browser_context_args(browser_context_args, smoke_auth_state):
    """Подставляет сессию от sign-up аккаунта вместо основного."""
    return {
        **browser_context_args,
        'ignore_https_errors': True,
        'storage_state': smoke_auth_state,
        'viewport': {'width': 1280, 'height': 720},
    }
