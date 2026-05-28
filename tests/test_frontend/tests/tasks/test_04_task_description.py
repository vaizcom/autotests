import allure
import pytest
from playwright.sync_api import Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, _TS, open_card, fill_description

pytestmark = [pytest.mark.frontend]

_DESCRIPTION = f"Test description {_TS}"


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Description")
@allure.title("01. Заполнить Description")
def test_01_fill_task_description(page: Page, soft_step):
    """Заполняет описание задачи."""
    open_card(page, soft_step, TASK_NAME)

    with allure.step(f"Ввод описания: {_DESCRIPTION}"):
        soft_step("Описание", lambda: fill_description(page, _DESCRIPTION))
