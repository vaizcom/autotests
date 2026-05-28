import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Auth, Header, Sidebar, SpaceSelector

pytestmark = [pytest.mark.frontend]


@pytest.fixture()
def browser_context_args(browser_context_args):
    """Убираем storage_state — тест логинится самостоятельно."""
    return {k: v for k, v in browser_context_args.items() if k != "storage_state"}


@allure.parent_suite("Frontend")
@allure.suite("Auth")
@allure.title("Logout")
def test_logout(page: Page, assert_snapshot):
    with allure.step("Вход в систему"):
        page.goto(f"{settings.BASE_URL}/auth/sign-in")
        page.get_by_test_id(Auth.EMAIL_INPUT).fill(settings.FRONTEND_EMAIL)
        page.get_by_test_id(Auth.EMAIL_SUBMIT).click()
        page.get_by_test_id(Auth.PASSWORD_INPUT).wait_for(state="visible", timeout=10000)
        page.get_by_test_id(Auth.PASSWORD_INPUT).fill(settings.FRONTEND_PASSWORD)
        page.get_by_test_id(Auth.PASSWORD_SUBMIT).click()
        expect(page.get_by_test_id(Sidebar.HOME)).to_be_visible(timeout=15000)

    with allure.step("Переход в autotest space"):
        page.get_by_test_id(Header.SPACE_SELECTOR).click()
        page.get_by_test_id(SpaceSelector.space(settings.AUTOTEST_SPACE_ID)).click()
        page.get_by_test_id(Sidebar.HOME).wait_for(state="visible", timeout=10000)

    with allure.step("Открытие меню пользователя"):
        page.get_by_test_id(Header.AVATAR).click()

    with allure.step("Нажатие Log Out"):
        page.get_by_text("Log Out").click()

    with allure.step("Проверка редиректа на страницу входа"):
        expect(page).to_have_url(re.compile(r".*/auth/sign-in"), timeout=15000)
        expect(page.get_by_test_id(Auth.EMAIL_SUBMIT)).to_be_visible()

    with allure.step("Сравнение скриншота"):
        dynamic_masks = [
            page.get_by_test_id(Auth.EMAIL_INPUT),
            page.locator('[class*="AuthLayout-module_SideBox"]'),
        ]
        screenshot = page.screenshot(mask=dynamic_masks)
        assert_snapshot(screenshot, name="logout_sign_in_page.png", threshold=3.0)
