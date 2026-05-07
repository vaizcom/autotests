import re
from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.milestones.conftest import (
    create_milestone_on_board,
    open_milestone,
    archive_milestone,
)
from tests.test_frontend.tests.tasks.conftest import add_comment, fill_description

pytestmark = [pytest.mark.frontend]

_DEP_CREATE = "test_01_create_milestone"

_TS = datetime.now().strftime("%H%M%S")
_MILESTONE_NAME = f"autotest_ms_{_TS}"
_SHORT_DESC = f"Short desc {_TS}"
_DESCRIPTION = f"Milestone description {_TS}"
_TASK_NAME = f"MS task {_TS}"
_COMMENT = f"MS comment {_TS}"
_DATE_START = "01.08.2030"
_DATE_DUE = "10.08.2030"


# ── 01. Создание майлстоуна ─────────────────────────────────────────


@pytest.mark.dependency(name=_DEP_CREATE)
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("01. Create milestone on board")
def test_01_create_milestone(page: Page, soft_step):
    """Создаёт майлстоун через вкладку Milestones на борде."""
    with allure.step(f"Создание майлстоуна: {_MILESTONE_NAME}"):
        soft_step("Создание майлстоуна", lambda: create_milestone_on_board(page, _MILESTONE_NAME))


# ── 02. Название ────────────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("02. Verify milestone name")
def test_02_name(page: Page, soft_step):
    """Проверяет что название майлстоуна отображается корректно."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step("Проверка названия"):
        soft_step("Название", lambda: (
            expect(page.get_by_role("heading", name=_MILESTONE_NAME)).to_be_visible(timeout=5000)
        ))


# ── 03. Короткое описание ──────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("03. Set short description")
def test_03_short_description(page: Page, soft_step):
    """Заполняет и проверяет короткое описание майлстоуна."""
    open_milestone(page, _MILESTONE_NAME)

    def set_short_desc():
        short_desc = page.get_by_placeholder("Enter short description...")
        short_desc.click()
        short_desc.fill(_SHORT_DESC)
        page.keyboard.press("Tab")
        expect(short_desc).to_have_value(_SHORT_DESC, timeout=5000)

    with allure.step(f"Короткое описание: {_SHORT_DESC}"):
        soft_step("Короткое описание", set_short_desc)


# ── 04. Описание (tiptap) ──────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("04. Set and verify description")
def test_04_description(page: Page, soft_step):
    """Заполняет и проверяет описание майлстоуна (tiptap-редактор после секции задач)."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step(f"Описание: {_DESCRIPTION}"):
        soft_step("Заполнение описания", lambda: fill_description(page, _DESCRIPTION))


# ── 05. Даты ────────────────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("05. Set and verify dates")
def test_05_dates(page: Page, soft_step):
    """Устанавливает и проверяет даты майлстоуна."""
    open_milestone(page, _MILESTONE_NAME)

    def set_dates():
        page.get_by_role("button", name="Dates No dates set").click()
        inputs = page.get_by_placeholder(re.compile(r"\d{2}\.\d{2}\.\d{4}"))
        inputs.first.fill(_DATE_START)
        inputs.last.fill(_DATE_DUE)
        page.get_by_role("button", name="Apply").click()

    with allure.step(f"Даты: {_DATE_START}"):
        soft_step("Установка дат", set_dates)

    with allure.step("Проверка дат"):
        soft_step("Даты сохранены", lambda: (
            expect(page.get_by_role("button", name=re.compile(r"Dates.*2030"))).to_be_visible(timeout=5000)
        ))


# ── 06. Секция задач ────────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("06. Add task to milestone")
def test_06_task_list(page: Page, soft_step):
    """Создаёт задачу в майлстоуне и проверяет что она появилась."""
    open_milestone(page, _MILESTONE_NAME)

    def add_task():
        task_input = page.get_by_role("textbox", name="Enter task name")
        task_input.click()
        task_input.fill(_TASK_NAME)
        page.keyboard.press("Enter")
        expect(
            page.get_by_role("button").filter(has_text=re.compile(r"[A-Z]+-\d+")).filter(has_text=_TASK_NAME)
        ).to_be_visible(timeout=10000)

    with allure.step(f"Создание задачи: {_TASK_NAME}"):
        soft_step("Создание задачи", add_task)


# ── 07. Комментарии ─────────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("07. Add comment and verify")
def test_07_comments(page: Page, soft_step):
    """Добавляет комментарий к майлстоуну и проверяет."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step(f"Комментарий: {_COMMENT}"):
        page.get_by_role("button", name=re.compile(r"Comments \d+")).click()
        soft_step("Добавление комментария", lambda: add_comment(page, _COMMENT))

    with allure.step("Проверка комментария"):
        soft_step("Комментарий сохранён", lambda: (
            expect(page.get_by_text(_COMMENT)).to_be_visible(timeout=5000)
        ))


# ── 08. Вкладка Activities ──────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("08. Verify Activities tab")
def test_08_activities(page: Page, soft_step):
    """Проверяет что вкладка Activities отображается."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step("Вкладка Activities видна"):
        soft_step("Вкладка Activities", lambda: (
            expect(page.get_by_role("button", name="Activities")).to_be_visible(timeout=5000)
        ))


# ── 99. Cleanup ─────────────────────────────────────────────────────


@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("99. Cleanup: archive milestone")
def test_99_cleanup(page: Page):
    """Удаляет задачи и архивирует тестовый майлстоун."""
    archive_milestone(page, _MILESTONE_NAME)
