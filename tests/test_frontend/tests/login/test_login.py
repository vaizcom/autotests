import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings

pytestmark = [pytest.mark.frontend]


@pytest.fixture()
def browser_context_args(browser_context_args):
    """Убираем storage_state — тест проверяет сам логин."""
    return {k: v for k, v in browser_context_args.items() if k != "storage_state"}


def test_sign_in_with_email(page: Page):
    with allure.step("Открытие страницы входа"):
        page.goto(f"{settings.BASE_URL}/auth/sign-in")

    with allure.step("Ввод учётных данных"):
        page.get_by_role("textbox", name="Email").fill(settings.FRONTEND_EMAIL)
        page.get_by_role("textbox", name="Password").fill(settings.FRONTEND_PASSWORD)

    with allure.step("Нажатие кнопки Continue with Email"):
        page.get_by_role("button", name="Continue with Email").click()

    with allure.step("Проверка успешного входа"):
        page.wait_for_load_state("networkidle")
        expect(page).not_to_have_url(f"{settings.BASE_URL}/auth/sign-in")
        expect(page.get_by_role("link", name="Home")).to_be_visible()
