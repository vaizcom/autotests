import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, open_card

pytestmark = [pytest.mark.frontend]


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Priority")
@allure.title("01. Установить Medium")
def test_01_set_task_priority(page: Page, soft_step, sidebar):
    """Устанавливает приоритет задачи Medium."""
    open_card(page, soft_step, TASK_NAME)

    def set_priority():
        sidebar.get_by_role("button", name="Priority Select priority").click()
        page.get_by_text("Medium").click()
        expect(sidebar.get_by_role("button", name=re.compile(r"Priority.*Medium"))).to_be_visible(timeout=5000)

    with allure.step("Выбор приоритета Medium"):
        soft_step("Приоритет", set_priority)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Priority")
@allure.title("02. Изменить: Medium → High")
def test_02_edit_task_priority(page: Page, soft_step, sidebar):
    """Меняет приоритет задачи с Medium на High."""
    open_card(page, soft_step, TASK_NAME)

    def edit_priority():
        sidebar.get_by_role("button", name=re.compile(r"Priority.*Medium")).click()
        page.get_by_text("High").click()
        expect(sidebar.get_by_role("button", name=re.compile(r"Priority.*High"))).to_be_visible(timeout=5000)

    with allure.step("Смена приоритета на High"):
        soft_step("Приоритет → High", edit_priority)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Priority")
@allure.title("03. Сбросить Priority")
def test_03_clear_task_priority(page: Page, soft_step, sidebar):
    """Снимает приоритет задачи."""
    open_card(page, soft_step, TASK_NAME)

    def clear_priority():
        sidebar.get_by_role("button", name=re.compile(r"Priority.*High")).click()
        page.get_by_text("Default").click()
        expect(sidebar.get_by_role("button", name="Priority Select priority")).to_be_visible(timeout=5000)

    with allure.step("Сброс приоритета"):
        soft_step("Приоритет → пусто", clear_priority)
