import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings

pytestmark = [pytest.mark.frontend]


@allure.parent_suite("Frontend")
@allure.suite("Auth")
@allure.title("Login after logout")
def test_login_after_logout(page: Page):
    with allure.step("Открытие главной страницы"):
        page.goto(f"{settings.BASE_URL}/")
        expect(page.get_by_role("link", name="Home")).to_be_visible(timeout=15000)

    with allure.step("Открытие меню пользователя"):
        page.locator('[class*="MemberAvatar-module_Root"]').first.click()

    with allure.step("Нажатие Log Out"):
        page.get_by_text("Log Out").click()

    with allure.step("Проверка редиректа на страницу входа"):
        expect(page).to_have_url(re.compile(r".*/auth/sign-in"), timeout=15000)

    with allure.step("Повторный вход"):
        page.get_by_role("textbox", name="Email").fill(settings.FRONTEND_EMAIL)
        page.get_by_role("textbox", name="Password").fill(settings.FRONTEND_PASSWORD)
        page.get_by_role("button", name="Continue with Email").click()

    with allure.step("Проверка успешного входа"):
        expect(page).not_to_have_url(f"{settings.BASE_URL}/auth/sign-in", timeout=15000)
        expect(page.get_by_role("link", name="Home")).to_be_visible(timeout=15000)
