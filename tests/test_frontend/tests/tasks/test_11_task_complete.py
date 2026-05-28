import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, open_card

pytestmark = [pytest.mark.frontend]


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Complete")
@allure.title("01. Завершить Task")
def test_01_complete_task(page: Page, soft_step, sidebar):
    """Отмечает задачу как выполненную (Complete)."""
    open_card(page, soft_step, TASK_NAME)

    def complete_task():
        checkbox = sidebar.locator('label[role="checkbox"]').first
        checkbox.click()
        expect(checkbox.locator("input")).to_be_checked(timeout=5000)

    with allure.step("Клик по чекбоксу Complete"):
        soft_step("Complete", complete_task)
