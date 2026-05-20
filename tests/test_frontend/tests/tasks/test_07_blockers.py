import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, _TS, open_card

pytestmark = [pytest.mark.frontend]

_BLOCKER_NAME = f"Blocker task {_TS}"
_BLOCKING_NAME = f"Blocking task {_TS}"


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Blockers")
@allure.title("01. Добавить Blocker и Blocking")
def test_01_add(page: Page, soft_step, sidebar):
    """Добавляет блокер и блокинг задачу."""
    open_card(page, soft_step, TASK_NAME)

    def add_blocker():
        sidebar.get_by_role("textbox", name="Add blocker").fill(_BLOCKER_NAME)
        sidebar.get_by_role("textbox", name="Add blocker").press("Enter")
        expect(sidebar.get_by_text(_BLOCKER_NAME).first).to_be_visible(timeout=10000)

    with allure.step(f"Создание блокера: {_BLOCKER_NAME}"):
        soft_step("Блокер", add_blocker)

    def add_blocking():
        sidebar.get_by_role("textbox", name="Add blocking").fill(_BLOCKING_NAME)
        sidebar.get_by_role("textbox", name="Add blocking").press("Enter")
        expect(sidebar.get_by_text(_BLOCKING_NAME).first).to_be_visible(timeout=10000)

    with allure.step(f"Создание блокинга: {_BLOCKING_NAME}"):
        soft_step("Блокинг", add_blocking)
