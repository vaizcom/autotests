import os
import re
from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.conftest import cleanup_board
from tests.test_frontend.tests.milestones.conftest import (
    create_milestone_on_board,
    open_milestone,
    add_task_to_milestone,
    wait_for_task_rows,
    archive_milestone,
    cleanup_milestones,
)
from tests.test_frontend.tests.tasks.conftest import add_comment, fill_description, set_date

pytestmark = [pytest.mark.frontend]

# test_01 — создаёт майлстоун, остальные зависят от него.
# При запуске отдельного теста через IDE — майлстоун создаётся и архивируется автоматически.
_DEP_CREATE = "test_01_create_milestone"
_DEP_TASK_LIST = "test_06_add_tasks"

_TS = os.environ.get("TEST_TS") or datetime.now().strftime("%H%M%S")
_MILESTONE_NAME = f"autotest_ms_{_TS}"
_SHORT_DESC = f"Short desc {_TS}"
_DESCRIPTION = f"Milestone description {_TS}"
_TASK_NAME = f"MS task {_TS}"
_TASK_NAME_2 = f"MS task 2 {_TS}"
_COMMENT = f"MS comment {_TS}"
_DATE_START = "01.08.2030"
_DATE_DUE = "10.08.2030"



# ── Auto-debug: setup/cleanup при запуске отдельного теста из IDE ──


def _debug_create(page):
    create_milestone_on_board(page, _MILESTONE_NAME)


_KEEP_MILESTONES = ["Test milestone"]


def _debug_teardown(page):
    cleanup_milestones(page, keep_names=_KEEP_MILESTONES)
    cleanup_board(page)


def _setup_tasks(page):
    for name in (_TASK_NAME, _TASK_NAME_2):
        add_task_to_milestone(page, name)


_debug_extra_setup = {
    "test_07_complete_tasks": _setup_tasks,
    "test_08_delete_tasks": _setup_tasks,
}


# ── 01. Создание майлстоуна ─────────────────────────────────────────


@pytest.mark.dependency(name=_DEP_CREATE)
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.sub_suite("Fields")
@allure.title("01. Create milestone on board")
def test_01_create_milestone(page: Page, soft_step):
    """Создаёт майлстоун через вкладку Milestones на борде."""
    with allure.step(f"Создание майлстоуна: {_MILESTONE_NAME}"):
        soft_step("Создание майлстоуна", lambda: create_milestone_on_board(page, _MILESTONE_NAME))


# ── 02. Название ────────────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.sub_suite("Fields")
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
@allure.sub_suite("Fields")
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
@allure.sub_suite("Fields")
@allure.title("04. Set and verify description")
def test_04_description(page: Page, soft_step):
    """Заполняет и проверяет описание майлстоуна (tiptap-редактор после секции задач)."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step(f"Описание: {_DESCRIPTION}"):
        soft_step("Заполнение описания", lambda: fill_description(page, _DESCRIPTION))

    with allure.step("Проверка описания"):
        soft_step("Описание сохранено", lambda: (
            expect(page.locator('.tiptap').filter(has_text=_DESCRIPTION).first).to_be_visible(timeout=5000)
        ))


# ── 05. Даты ────────────────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.sub_suite("Fields")
@allure.title("05. Set and verify dates")
def test_05_dates(page: Page, soft_step):
    """Устанавливает и проверяет даты майлстоуна."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step(f"Даты: {_DATE_START}"):
        soft_step("Установка дат", lambda: set_date(page, date=_DATE_START))

    with allure.step("Проверка дат"):
        soft_step("Даты сохранены", lambda: (
            expect(page.get_by_role("button", name=re.compile(r"Dates.*2030"))).to_be_visible(timeout=5000)
        ))


# ── 06. Добавление задач + счётчики ────────────────────────────────


@pytest.mark.dependency(name=_DEP_TASK_LIST, depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.sub_suite("Fields")
@allure.title("06. Add tasks and verify counters")
def test_06_add_tasks(page: Page, soft_step):
    """Добавляет две задачи в майлстоун, проверяет счётчик на каждом шаге."""
    open_milestone(page, _MILESTONE_NAME)

    # ── Пустое состояние ──

    with allure.step("Проверка: 0 tasks"):
        soft_step("0 tasks", lambda: (
            expect(page.get_by_role("heading", name="0 tasks")).to_be_visible(timeout=5000)
        ))

    # ── Задача 1 → "1 task" + "0 completed of 1" ──

    with allure.step(f"Добавление задачи: {_TASK_NAME}"):
        soft_step("Добавление задачи 1", lambda: add_task_to_milestone(page, _TASK_NAME))

    with allure.step("Проверка: 1 task"):
        soft_step("1 task", lambda: (
            expect(page.get_by_role("heading", name=re.compile(r"\b1 task\b"))).to_be_visible(timeout=5000)
        ))

    with allure.step("Проверка: 0 completed of 1"):
        soft_step("0 completed of 1", lambda: (
            expect(page.get_by_text("0 completed of 1")).to_be_visible(timeout=5000)
        ))

    # ── Задача 2 → "2 tasks" + "0 completed of 2" ──

    with allure.step(f"Добавление задачи: {_TASK_NAME_2}"):
        soft_step("Добавление задачи 2", lambda: add_task_to_milestone(page, _TASK_NAME_2))

    with allure.step("Проверка: 2 tasks"):
        soft_step("2 tasks", lambda: (
            expect(page.get_by_role("heading", name="2 tasks")).to_be_visible(timeout=5000)
        ))

    with allure.step("Проверка: 0 completed of 2"):
        soft_step("0 completed of 2", lambda: (
            expect(page.get_by_text("0 completed of 2")).to_be_visible(timeout=5000)
        ))


# ── 07. Завершение / снятие завершения задач ───────────────────────


@pytest.mark.dependency(depends=[_DEP_TASK_LIST])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.sub_suite("Fields")
@allure.title("07. Verify task completion counters")
def test_07_complete_tasks(page: Page, soft_step):
    """Завершает и снимает завершение задач, проверяет счётчики."""
    open_milestone(page, _MILESTONE_NAME)
    wait_for_task_rows(page, _MILESTONE_NAME)

    def toggle_complete(task_name):
        task_row = (
            page.get_by_role("button")
            .filter(has_text=re.compile(r"[A-Z]+-\d+"))
            .filter(has_text=task_name)
        )
        task_row.locator('label[role="checkbox"]').click()

    # ── Complete задачи 1 → "1 completed of 2" ──

    with allure.step(f"Завершение задачи: {_TASK_NAME}"):
        soft_step("Завершение задачи 1", lambda: toggle_complete(_TASK_NAME))

    with allure.step("Проверка: 1 completed of 2"):
        soft_step("1 completed of 2", lambda: (
            expect(page.get_by_text("1 completed of 2")).to_be_visible(timeout=5000)
        ))

    # ── Complete задачи 2 → "All 2 completed" ──

    with allure.step(f"Завершение задачи: {_TASK_NAME_2}"):
        soft_step("Завершение задачи 2", lambda: toggle_complete(_TASK_NAME_2))

    with allure.step("Проверка: All 2 completed"):
        soft_step("All 2 completed", lambda: (
            expect(page.get_by_text("All 2 completed")).to_be_visible(timeout=5000)
        ))

    # ── Uncomplete задачи 1 → "1 completed of 2" ──

    with allure.step(f"Снятие завершения: {_TASK_NAME}"):
        soft_step("Снятие завершения задачи 1", lambda: toggle_complete(_TASK_NAME))

    with allure.step("Проверка: 1 completed of 2 (после снятия)"):
        soft_step("1 completed of 2 (после снятия)", lambda: (
            expect(page.get_by_text("1 completed of 2")).to_be_visible(timeout=5000)
        ))

    # ── Uncomplete задачи 2 → "0 completed of 2" ──

    with allure.step(f"Снятие завершения: {_TASK_NAME_2}"):
        soft_step("Снятие завершения задачи 2", lambda: toggle_complete(_TASK_NAME_2))

    with allure.step("Проверка: 0 completed of 2"):
        soft_step("0 completed of 2", lambda: (
            expect(page.get_by_text("0 completed of 2")).to_be_visible(timeout=5000)
        ))


# ── 08. Удаление задач + счётчики ──────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_TASK_LIST])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.sub_suite("Fields")
@allure.title("08. Delete tasks and verify counters")
def test_08_delete_tasks(page: Page, soft_step):
    """Удаляет задачи из таблицы майлстоуна, проверяет уменьшение счётчика."""
    open_milestone(page, _MILESTONE_NAME)
    wait_for_task_rows(page, _MILESTONE_NAME)

    def delete_task(task_name):
        task_row = (
            page.get_by_role("button")
            .filter(has_text=re.compile(r"[A-Z]+-\d+"))
            .filter(has_text=task_name)
        )
        task_row.get_by_role("button").nth(1).click()
        page.get_by_text("Delete task").click()
        page.get_by_role("button", name="Proceed").click()

    # ── Удаление задачи 1 → "1 task" ──

    with allure.step(f"Удаление задачи: {_TASK_NAME}"):
        soft_step("Удаление задачи 1", lambda: delete_task(_TASK_NAME))

    with allure.step("Проверка: 1 task"):
        soft_step("1 task", lambda: (
            expect(page.get_by_role("heading", name=re.compile(r"\b1 task\b"))).to_be_visible(timeout=5000)
        ))

    # ── Удаление задачи 2 → "0 tasks" ──

    with allure.step(f"Удаление задачи: {_TASK_NAME_2}"):
        soft_step("Удаление задачи 2", lambda: delete_task(_TASK_NAME_2))

    with allure.step("Проверка: 0 tasks"):
        soft_step("0 tasks", lambda: (
            expect(page.get_by_role("heading", name="0 tasks")).to_be_visible(timeout=5000)
        ))


# ── 09. Комментарии ─────────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.sub_suite("Fields")
@allure.title("09. Add comment and verify")
def test_09_comments(page: Page, soft_step):
    """Добавляет комментарий к майлстоуну и проверяет."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step(f"Комментарий: {_COMMENT}"):
        page.get_by_role("button", name=re.compile(r"Comments \d+")).click()
        soft_step("Добавление комментария", lambda: add_comment(page, _COMMENT))

    with allure.step("Проверка комментария"):
        soft_step("Комментарий сохранён", lambda: (
            expect(page.get_by_text(_COMMENT)).to_be_visible(timeout=5000)
        ))


# ── 10. Вкладка Activities ─────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.sub_suite("Fields")
@allure.title("10. Verify Activities tab")
def test_10_activities(page: Page, soft_step):
    """Проверяет что вкладка Activities отображается."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step("Вкладка Activities видна"):
        soft_step("Вкладка Activities", lambda: (
            expect(page.get_by_role("button", name="Activities")).to_be_visible(timeout=5000)
        ))


# ── 99. Cleanup ─────────────────────────────────────────────────────


@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.sub_suite("Fields")
@allure.title("99. Cleanup: archive milestone")
def test_99_cleanup(page: Page):
    """Удаляет задачи и архивирует тестовый майлстоун."""
    archive_milestone(page, _MILESTONE_NAME)
