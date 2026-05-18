import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Header, Sidebar, SpaceSelector

pytestmark = [pytest.mark.frontend]

_SPACE_NAME = settings.AUTOTEST_SPACE_NAME
_PROJECT_NAME = settings.AUTOTEST_PROJECT_NAME


@allure.parent_suite("Frontend")
@allure.suite("Spaces")
@allure.title("Space and project navigation")
def test_navigation(page: Page, soft_step):
    """Проверяет навигацию: выбор спейса, видимость проекта, открытие проекта."""
    with allure.step("Открытие Home"):
        page.goto(f"{settings.BASE_URL}/")
        expect(page.get_by_test_id(Sidebar.HOME)).to_be_visible(timeout=15000)

    with allure.step(f"Открытие {_SPACE_NAME}"):
        soft_step("Выбор спейса", lambda: (
            page.get_by_test_id(Header.SPACE_SELECTOR).click() or
            page.get_by_test_id(SpaceSelector.space(settings.AUTOTEST_SPACE_ID)).click()
        ))
        expect(page).to_have_url(re.compile(r".+/[a-f0-9]+"), timeout=10000)

    with allure.step(f"Проверка видимости {_PROJECT_NAME}"):
        soft_step("Проект виден", lambda: (
            expect(page.locator("span").filter(has_text=_PROJECT_NAME)).to_be_visible(timeout=10000)
        ))

    with allure.step(f"Открытие {_PROJECT_NAME}"):
        soft_step("Открытие проекта", lambda: (
            page.locator("span").filter(has_text=_PROJECT_NAME).get_by_role("link").click()
        ))
        expect(page.get_by_text("Add board")).to_be_visible(timeout=10000)
