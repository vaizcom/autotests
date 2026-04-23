import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings

pytestmark = [pytest.mark.frontend]


@allure.parent_suite("Frontend")
@allure.suite("Auth")
@allure.title("Logout")
def test_logout(page: Page, assert_snapshot):
    with allure.step("Открытие главной страницы"):
        page.goto(f"{settings.BASE_URL}/")
        expect(page.get_by_role("link", name="Home")).to_be_visible(timeout=15000)

    with allure.step("Открытие меню пользователя"):
        page.locator('[class*="MemberAvatar-module_Root"]').first.click()

    with allure.step("Нажатие Log Out"):
        page.get_by_text("Log Out").click()

    with allure.step("Проверка редиректа на страницу входа"):
        expect(page).to_have_url(re.compile(r".*/auth/sign-in"), timeout=15000)
        expect(page.get_by_role("button", name="Continue with Email")).to_be_visible()

    with allure.step("Сравнение скриншота"):
        dynamic_masks = [
            page.get_by_role("textbox", name="Email"),
        ]
        screenshot = page.screenshot(mask=dynamic_masks)
        assert_snapshot(screenshot, name="logout_sign_in_page.png", threshold=0.5)
