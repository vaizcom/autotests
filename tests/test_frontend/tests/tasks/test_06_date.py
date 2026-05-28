from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, open_card, set_date, future_date

pytestmark = [pytest.mark.frontend]

_DATE = future_date(10)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Date")
@allure.title("01. Установить Date")
def test_01_set_date_task(page: Page, soft_step, sidebar):
    """Устанавливает дату задачи."""
    open_card(page, soft_step, TASK_NAME)

    with allure.step(f"Установка даты {_DATE}"):
        soft_step("Дата", lambda: set_date(page, _DATE))

    with allure.step("Проверка даты"):
        _d = datetime.strptime(_DATE, "%d.%m.%Y")
        _expected = f"{_d.day} {_d.strftime('%b')} {_d.strftime('%y')}"
        soft_step("Дата сохранена", lambda: (
            expect(sidebar.get_by_text(_expected)).to_be_visible(timeout=5000)
        ))
