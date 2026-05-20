import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, open_card

pytestmark = [pytest.mark.frontend]


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Assignee")
@allure.title("01. Назначить Assignee")
def test_01_assign(page: Page, soft_step, sidebar):
    """Назначает первого пользователя из списка исполнителем."""
    open_card(page, soft_step, TASK_NAME)

    def assign():
        sidebar.get_by_role("button", name="Assign Not assigned").click()
        page.locator('.szh-menu-container [class*="SelectFlySearch-module_ItemText"]').first.click()
        page.locator('[class*="FlyBlock-module_Overlay"]').click()
        expect(sidebar.get_by_role("button", name=re.compile(r"Assign\s+\S"))).to_be_visible(timeout=5000)

    with allure.step("Выбор исполнителя"):
        soft_step("Исполнитель", assign)
