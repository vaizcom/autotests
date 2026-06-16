import time

import allure
import pytest
from playwright.sync_api import Page

from tests.test_frontend.tests.auth.conftest import (
    sign_up_new_account,
    home_screenshot_with_masks,
)

pytestmark = [pytest.mark.frontend]


@allure.parent_suite('Frontend')
@allure.suite('Auth')
@allure.title('Sign up with email (OTP)')
def test_sign_up_with_email(page: Page, db, assert_snapshot):
    ts = int(time.time())
    new_email = f'TST_autotest_{ts}@mailinator.com'

    with allure.step(f'Регистрация нового аккаунта: {new_email}'):
        sign_up_new_account(page, new_email, db=db)

    with allure.step('Сравнение скриншота'):
        screenshot = home_screenshot_with_masks(page)
        assert_snapshot(screenshot, name='sign_up_home.png', threshold=5.0)
