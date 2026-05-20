import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, open_card

pytestmark = [pytest.mark.frontend]


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Type")
@allure.title("01. Установить Type Green")
def test_01_set(page: Page, soft_step, sidebar):
    """Устанавливает тип задачи Green."""
    open_card(page, soft_step, TASK_NAME)

    def set_type():
        sidebar.get_by_role("button", name="Types Select type").click()
        page.get_by_role("menuitem", name="Green").click()
        expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Green"))).to_be_visible(timeout=5000)

    with allure.step("Выбор типа Green"):
        soft_step("Тип", set_type)
