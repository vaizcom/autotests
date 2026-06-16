import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core.locators import Auth, Header
from tests.test_frontend.tests.auth.conftest import sign_in_and_go_to_space

pytestmark = [pytest.mark.frontend]


@allure.parent_suite('Frontend')
@allure.suite('Auth')
@allure.title('Logout')
def test_logout(page: Page, assert_snapshot):
    with allure.step('Вход и переход в autotest space'):
        sign_in_and_go_to_space(page)

    with allure.step('Открытие меню пользователя'):
        page.get_by_test_id(Header.AVATAR).click()

    with allure.step('Нажатие Log Out'):
        page.get_by_text('Log Out').click()

    with allure.step('Проверка редиректа на страницу входа'):
        expect(page).to_have_url(re.compile(r'.*/auth/sign-in'), timeout=15000)
        expect(page.get_by_test_id(Auth.EMAIL_SUBMIT)).to_be_visible()

    with allure.step('Сравнение скриншота'):
        dynamic_masks = [
            page.get_by_test_id(Auth.EMAIL_INPUT),
            page.locator('[class*="AuthLayout-module_SideBox"]'),
        ]
        screenshot = page.screenshot(mask=dynamic_masks)
        assert_snapshot(screenshot, name='logout_sign_in_page.png', threshold=3.0)
