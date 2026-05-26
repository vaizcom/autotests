import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, open_card, set_date

pytestmark = [pytest.mark.frontend]


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Date")
@allure.title("01. Установить Date")
def test_01_set(page: Page, soft_step, sidebar):
    """Устанавливает дату задачи."""
    open_card(page, soft_step, TASK_NAME)

    with allure.step("Установка даты 10.08.2030"):
        soft_step("Дата", lambda: set_date(page, "10.08.2030"))

    with allure.step("Проверка даты"):
        soft_step("Дата сохранена", lambda: (
            expect(sidebar.get_by_text(re.compile(r"10 Aug 30"))).to_be_visible(timeout=5000)
        ))
