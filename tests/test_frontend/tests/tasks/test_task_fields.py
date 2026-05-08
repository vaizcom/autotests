import os
import re
from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.conftest import cleanup_board
from tests.test_frontend.tests.tasks.conftest import open_card, create_task_on_board, add_subtask, create_subtasks, toggle_subtask_complete, set_date, add_comment, fill_description

pytestmark = [pytest.mark.frontend]

# test_01 — создаёт задачу, остальные зависят от неё.
# При падении test_01 зависимые тесты будут SKIP, а не FAIL.
# При запуске отдельного теста через IDE — задача создаётся и удаляется автоматически.
_DEP_TASK = "test_01_create_task"
_DEP_SUBTASK = "test_11_add_subtasks"

_TS = os.environ.get("TEST_TS") or datetime.now().strftime("%H%M%S")
_TASK_NAME = f"autotest_{_TS}"
_SUBTASK_NAME = f"Test subtask {_TS}"
_SUBTASK_NAME_2 = f"Test subtask 2 {_TS}"
_DESCRIPTION = f"Test description {_TS}"
_COMMENT = f"Test comment {_TS}"
_MILESTONE_NAME = "Test milestone"
_BLOCKER_NAME = f"Blocker task {_TS}"
_BLOCKING_NAME = f"Blocking task {_TS}"
_CUSTOM_TEXT_VALUE = f"Test value {_TS}"



# ── Auto-debug: setup/cleanup при запуске отдельного теста из IDE ──


def _debug_create(page):
    create_task_on_board(page, _TASK_NAME)


def _debug_teardown(page):
    cleanup_board(page)


def _setup_subtasks(page):
    create_subtasks(page, _TASK_NAME, [_SUBTASK_NAME, _SUBTASK_NAME_2])


_debug_extra_setup = {
    "test_12_complete_subtasks": _setup_subtasks,
    "test_13_delete_subtasks": _setup_subtasks,
}


@pytest.mark.dependency(name=_DEP_TASK)
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("01. Create task on board")
def test_01_create_task(page: Page, soft_step):
    """Создаёт новую задачу на борде и проверяет что карточка появилась."""
    with allure.step(f"Создание задачи: {_TASK_NAME}"):
        soft_step("Создание задачи", lambda: create_task_on_board(page, _TASK_NAME))


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("02. Set priority Medium")
def test_02_priority(page: Page, soft_step):
    """Устанавливает приоритет задачи Medium."""
    open_card(page, soft_step, _TASK_NAME)

    def set_priority():
        page.get_by_role("button", name="Priority Select priority").click()
        page.get_by_text("Medium").click()
        expect(page.get_by_role("button", name=re.compile(r"Priority.*Medium"))).to_be_visible(timeout=5000)

    with allure.step("Выбор приоритета Medium"):
        soft_step("Приоритет", set_priority)


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("03. Assign user")
def test_03_assignee(page: Page, soft_step):
    """Назначает первого пользователя из списка исполнителем."""
    open_card(page, soft_step, _TASK_NAME)

    def assign():
        page.get_by_role("button", name="Assign Not assigned").click()
        page.locator('.szh-menu-container [class*="SelectFlySearch-module_ItemText"]').first.click()
        page.locator('[class*="FlyBlock-module_Overlay"]').click()
        expect(page.get_by_role("button", name=re.compile(r"Assign\s+\S"))).to_be_visible(timeout=5000)

    with allure.step("Выбор исполнителя"):
        soft_step("Исполнитель", assign)


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("04. Set type Green")
def test_04_type(page: Page, soft_step):
    """Устанавливает тип задачи Green."""
    open_card(page, soft_step, _TASK_NAME)

    def set_type():
        page.get_by_role("button", name="Types Select type").click()
        page.get_by_role("menuitem", name="Green").click()
        expect(page.get_by_role("button", name=re.compile(r"Types.*Green"))).to_be_visible(timeout=5000)

    with allure.step("Выбор типа Green"):
        soft_step("Тип", set_type)


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("05. Fill description")
def test_05_description(page: Page, soft_step):
    """Заполняет описание задачи."""
    open_card(page, soft_step, _TASK_NAME)

    with allure.step(f"Ввод описания: {_DESCRIPTION}"):
        soft_step("Описание", lambda: fill_description(page, _DESCRIPTION))


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("06. Add milestone")
def test_06_milestone(page: Page, soft_step):
    """Привязывает майлстоун к задаче."""
    open_card(page, soft_step, _TASK_NAME)

    def add_milestone():
        page.get_by_role("button", name="Milestones Select milestones").click()
        page.get_by_role("textbox", name="Type to search...").fill(_MILESTONE_NAME)
        page.get_by_role("menuitem", name=_MILESTONE_NAME).click()
        expect(page.get_by_role("button", name=re.compile(rf"Milestones.*{_MILESTONE_NAME}"))).to_be_visible(timeout=5000)

    with allure.step(f"Выбор майлстоуна: {_MILESTONE_NAME}"):
        soft_step("Майлстоун", add_milestone)


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("07. Set date")
def test_07_date(page: Page, soft_step):
    """Устанавливает дату задачи."""
    open_card(page, soft_step, _TASK_NAME)

    with allure.step("Установка даты 10.08.2030"):
        soft_step("Дата", lambda: set_date(page, "10.08.2030"))

    with allure.step("Проверка даты"):
        soft_step("Дата сохранена", lambda: (
            expect(page.get_by_role("button", name="Dates No dates set")).not_to_be_visible(timeout=5000)
        ))


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("08. Add blocker and blocking")
def test_08_blockers(page: Page, soft_step):
    """Добавляет блокер и блокинг задачу."""
    open_card(page, soft_step, _TASK_NAME)

    def add_blocker():
        page.get_by_role("textbox", name="Add blocker").fill(_BLOCKER_NAME)
        page.get_by_role("textbox", name="Add blocker").press("Enter")
        expect(page.get_by_text(_BLOCKER_NAME).first).to_be_visible(timeout=10000)

    with allure.step(f"Создание блокера: {_BLOCKER_NAME}"):
        soft_step("Блокер", add_blocker)

    def add_blocking():
        page.get_by_role("textbox", name="Add blocking").fill(_BLOCKING_NAME)
        page.get_by_role("textbox", name="Add blocking").press("Enter")
        expect(page.get_by_text(_BLOCKING_NAME).first).to_be_visible(timeout=10000)

    with allure.step(f"Создание блокинга: {_BLOCKING_NAME}"):
        soft_step("Блокинг", add_blocking)


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("09. Fill custom text field")
def test_09_custom_field(page: Page, soft_step):
    """Заполняет кастомное текстовое поле задачи."""
    open_card(page, soft_step, _TASK_NAME)

    def fill_custom_text():
        page.get_by_role("button", name=re.compile(r"^Text")).first.click()
        text_input = page.get_by_placeholder("Empty").first
        text_input.clear()
        text_input.fill(_CUSTOM_TEXT_VALUE)
        page.keyboard.press("Escape")

    with allure.step(f"Заполнение кастомного поля: {_CUSTOM_TEXT_VALUE}"):
        soft_step("Кастомное поле Text", fill_custom_text)


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("10. Add comment")
def test_10_comment(page: Page, soft_step):
    """Добавляет комментарий к задаче."""
    open_card(page, soft_step, _TASK_NAME)

    with allure.step(f"Комментарий: {_COMMENT}"):
        soft_step("Комментарий", lambda: add_comment(page, _COMMENT))


# ── 11. Добавление подзадач + счётчики ─────────────────────────────


@pytest.mark.dependency(name=_DEP_SUBTASK, depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("11. Add subtasks and verify counters")
def test_11_add_subtasks(page: Page, soft_step):
    """Добавляет две подзадачи, проверяет счётчик на каждом шаге."""
    open_card(page, soft_step, _TASK_NAME)

    # ── Пустое состояние ──

    with allure.step("Проверка: 0 subtasks"):
        soft_step("0 subtasks", lambda: (
            expect(page.get_by_role("heading", name="0 subtasks")).to_be_visible(timeout=5000)
        ))

    # ── Подзадача 1 → "1 subtask" + "0 completed of 1" ──

    with allure.step(f"Добавление подзадачи: {_SUBTASK_NAME}"):
        soft_step("Добавление подзадачи 1", lambda: add_subtask(page, _SUBTASK_NAME))

    with allure.step("Проверка: 1 subtask"):
        soft_step("1 subtask", lambda: (
            expect(page.get_by_role("heading", name=re.compile(r"\b1 subtask\b"))).to_be_visible(timeout=5000)
        ))

    with allure.step("Проверка: 0 completed of 1"):
        soft_step("0 completed of 1", lambda: (
            expect(page.get_by_text("0 completed of 1")).to_be_visible(timeout=5000)
        ))

    # ── Подзадача 2 → "2 subtasks" + "0 completed of 2" ──

    with allure.step(f"Добавление подзадачи: {_SUBTASK_NAME_2}"):
        soft_step("Добавление подзадачи 2", lambda: add_subtask(page, _SUBTASK_NAME_2))

    with allure.step("Проверка: 2 subtasks"):
        soft_step("2 subtasks", lambda: (
            expect(page.get_by_role("heading", name="2 subtasks")).to_be_visible(timeout=5000)
        ))

    with allure.step("Проверка: 0 completed of 2"):
        soft_step("0 completed of 2", lambda: (
            expect(page.get_by_text("0 completed of 2")).to_be_visible(timeout=5000)
        ))


# ── 12. Завершение / снятие завершения подзадач ────────────────────


@pytest.mark.dependency(depends=[_DEP_SUBTASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("12. Verify subtask completion counters")
def test_12_complete_subtasks(page: Page, soft_step):
    """Завершает и снимает завершение подзадач, проверяет счётчики."""
    open_card(page, soft_step, _TASK_NAME)

    # Скроллим к секции подзадач
    page.get_by_role("heading", name=re.compile(r"\d+ subtasks?")).scroll_into_view_if_needed()

    # ── Complete подзадачи 1 → "1 completed of 2" ──

    with allure.step(f"Завершение подзадачи: {_SUBTASK_NAME}"):
        soft_step("Завершение подзадачи 1", lambda: toggle_subtask_complete(page, _SUBTASK_NAME))

    with allure.step("Проверка: 1 completed of 2"):
        soft_step("1 completed of 2", lambda: (
            expect(page.get_by_text("1 completed of 2")).to_be_visible(timeout=5000)
        ))

    # ── Complete подзадачи 2 → "All 2 completed" ──

    with allure.step(f"Завершение подзадачи: {_SUBTASK_NAME_2}"):
        soft_step("Завершение подзадачи 2", lambda: toggle_subtask_complete(page, _SUBTASK_NAME_2))

    with allure.step("Проверка: All 2 completed"):
        soft_step("All 2 completed", lambda: (
            expect(page.get_by_text("All 2 completed")).to_be_visible(timeout=5000)
        ))

    # ── Uncomplete подзадачи 1 → "1 completed of 2" ──

    with allure.step(f"Снятие завершения: {_SUBTASK_NAME}"):
        soft_step("Снятие завершения подзадачи 1", lambda: toggle_subtask_complete(page, _SUBTASK_NAME))

    with allure.step("Проверка: 1 completed of 2 (после снятия)"):
        soft_step("1 completed of 2 (после снятия)", lambda: (
            expect(page.get_by_text("1 completed of 2")).to_be_visible(timeout=5000)
        ))

    # ── Uncomplete подзадачи 2 → "0 completed of 2" ──

    with allure.step(f"Снятие завершения: {_SUBTASK_NAME_2}"):
        soft_step("Снятие завершения подзадачи 2", lambda: toggle_subtask_complete(page, _SUBTASK_NAME_2))

    with allure.step("Проверка: 0 completed of 2"):
        soft_step("0 completed of 2", lambda: (
            expect(page.get_by_text("0 completed of 2")).to_be_visible(timeout=5000)
        ))


# ── 13. Удаление подзадач + счётчики ──────────────────────────────


@pytest.mark.dependency(depends=[_DEP_SUBTASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("13. Delete subtasks and verify counters")
def test_13_delete_subtasks(page: Page, soft_step):
    """Удаляет подзадачи из таблицы задачи, проверяет уменьшение счётчика."""
    open_card(page, soft_step, _TASK_NAME)

    def delete_subtask(subtask_name):
        subtask_row = (
            page.get_by_role("button")
            .filter(has_text=re.compile(r"[A-Z]+-\d+"))
            .filter(has_text=subtask_name)
        )
        expect(subtask_row).to_be_visible(timeout=10000)
        subtask_row.get_by_role("button").nth(1).click()
        page.get_by_text("Delete task").click()
        page.get_by_role("button", name="Proceed").click()

    # ── Удаление подзадачи 1 → "1 subtask" ──

    with allure.step(f"Удаление подзадачи: {_SUBTASK_NAME}"):
        soft_step("Удаление подзадачи 1", lambda: delete_subtask(_SUBTASK_NAME))

    with allure.step("Проверка: 1 subtask"):
        soft_step("1 subtask", lambda: (
            expect(page.get_by_role("heading", name=re.compile(r"\b1 subtask\b"))).to_be_visible(timeout=5000)
        ))

    # ── Удаление подзадачи 2 → "0 subtasks" ──

    with allure.step(f"Удаление подзадачи: {_SUBTASK_NAME_2}"):
        soft_step("Удаление подзадачи 2", lambda: delete_subtask(_SUBTASK_NAME_2))

    with allure.step("Проверка: 0 subtasks"):
        soft_step("0 subtasks", lambda: (
            expect(page.get_by_role("heading", name="0 subtasks")).to_be_visible(timeout=5000)
        ))


# ── 14. Complete задачи ────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("14. Complete task")
def test_14_complete(page: Page, soft_step):
    """Отмечает задачу как выполненную (Complete)."""
    open_card(page, soft_step, _TASK_NAME)

    def complete_task():
        sidebar = page.locator('[class*="RightSidebar-module_Root"]')
        checkbox = sidebar.locator('label[role="checkbox"]').first
        checkbox.click()
        expect(checkbox.locator("input")).to_be_checked(timeout=5000)

    with allure.step("Клик по чекбоксу Complete"):
        soft_step("Complete", complete_task)


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Fields")
@allure.title("99. Cleanup: delete test tasks")
def test_99_cleanup(page: Page, cleanup_task):
    """Удаляет все карточки с таймстемпом теста с борды."""
    cleanup_task["ts"] = _TS
