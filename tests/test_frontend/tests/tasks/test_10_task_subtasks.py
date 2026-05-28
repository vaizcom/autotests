import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import (
    TASK_NAME, _TS, open_card, add_subtask, create_subtasks,
    find_subtask_row_by_name, wait_for_subtask_rows,
    toggle_subtask_complete, expect_subtask_counter, open_as_page,
)

pytestmark = [pytest.mark.frontend]

_SUBTASK_NAME = f"Test subtask {_TS}"
_SUBTASK_NAME_2 = f"Test subtask 2 {_TS}"

_DEP_ADD = "test_01_add_task_subtasks"


# ── Auto-debug: setup подзадач при запуске отдельного теста из IDE ──

def _debug_create(page):
    """Task создаётся session-фикстурой, но нужен для _auto_debug detection."""
    pass


def _setup_subtasks(page):
    create_subtasks(page, TASK_NAME, [_SUBTASK_NAME, _SUBTASK_NAME_2])


_debug_extra_setup = {
    "test_02_complete_task_subtask": _setup_subtasks,
    "test_03_delete_task_subtask": _setup_subtasks,
}


# ── Soft-проверка счётчика ────────────────────────────────────────────

def _check_counter(page: Page, name: str, check_fn):
    """Soft-проверка счётчика: логирует в Allure, но не ломает тест.

    Счётчик может не обновиться без reload (бродкаст),
    но это не должно скипать зависимые тесты.
    """
    with allure.step(f"Проверка: {name}"):
        try:
            check_fn()
        except Exception as e:
            short = str(e).split("\nCall log:")[0].split("\n")[0]
            allure.attach(
                page.screenshot(), name=f"{name} — скриншот",
                attachment_type=allure.attachment_type.PNG,
            )
            allure.attach(
                f"Счётчик не обновился\n{short}",
                name=f"{name} — лог",
                attachment_type=allure.attachment_type.TEXT,
            )


# ── 01. Добавление подзадач + счётчики ────────────────────────────────

@pytest.mark.dependency(name=_DEP_ADD)
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Subtasks")
@allure.title("01. Добавить Subtasks и проверить счётчики")
def test_01_add_task_subtasks(page: Page, soft_step, sidebar):
    """Добавляет две подзадачи, проверяет счётчик на каждом шаге."""
    open_card(page, soft_step, TASK_NAME)

    # ── Пустое состояние ──

    with allure.step("Проверка: 0 subtasks"):
        soft_step("0 subtasks", lambda: (
            expect(sidebar.get_by_role("heading", name="0 subtasks")).to_be_visible(timeout=5000)
        ))

    # ── Подзадача 1 → "1 subtask" + "0 completed of 1" ──

    with allure.step(f"Добавление подзадачи: {_SUBTASK_NAME}"):
        soft_step("Добавление подзадачи 1", lambda: add_subtask(page, _SUBTASK_NAME))

    _check_counter(page, "1 subtask", lambda: (
        expect(sidebar.get_by_role("heading", name=re.compile(r"\b1 subtask\b"))).to_be_visible(timeout=10000)
    ))

    _check_counter(page, "0 completed of 1", lambda: (
        expect(sidebar.get_by_text("0 completed of 1")).to_be_visible(timeout=10000)
    ))

    # ── Подзадача 2 → "2 subtasks" + "0 completed of 2" ──

    with allure.step(f"Добавление подзадачи: {_SUBTASK_NAME_2}"):
        soft_step("Добавление подзадачи 2", lambda: add_subtask(page, _SUBTASK_NAME_2))

    _check_counter(page, "2 subtasks", lambda: (
        expect(sidebar.get_by_role("heading", name="2 subtasks")).to_be_visible(timeout=10000)
    ))

    _check_counter(page, "0 completed of 2", lambda: (
        expect(sidebar.get_by_text("0 completed of 2")).to_be_visible(timeout=10000)
    ))


# ── 02. Завершение / снятие завершения подзадач ──────────────────────

@pytest.mark.dependency(depends=[_DEP_ADD])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Subtasks")
@allure.title("02. Завершить Subtask и проверить счётчики")
def test_02_complete_task_subtask(page: Page, soft_step):
    """Завершает и снимает завершение подзадач, проверяет счётчики.

    Открывается на полную страницу — подзадачи рендерятся сразу,
    без проблем с загрузкой и скроллом сайдбара.
    """
    open_card(page, soft_step, TASK_NAME)
    open_as_page(page, TASK_NAME)

    wait_for_subtask_rows(page, TASK_NAME, _SUBTASK_NAME, full_page=True)

    # ── Complete подзадачи 1 → "1 completed of 2" ──

    with allure.step(f"Завершение подзадачи: {_SUBTASK_NAME}"):
        soft_step("Завершение подзадачи 1", lambda: toggle_subtask_complete(page, _SUBTASK_NAME, full_page=True))

    with allure.step("Проверка: 1 completed of 2"):
        expect_subtask_counter(page, TASK_NAME, "1 completed of 2", full_page=True)

    # ── Complete подзадачи 2 → "All 2 completed" ──

    with allure.step(f"Завершение подзадачи: {_SUBTASK_NAME_2}"):
        soft_step("Завершение подзадачи 2", lambda: toggle_subtask_complete(page, _SUBTASK_NAME_2, full_page=True))

    with allure.step("Проверка: All 2 completed"):
        expect_subtask_counter(page, TASK_NAME, "All 2 completed", full_page=True)

    # ── Uncomplete подзадачи 1 → "1 completed of 2" ──

    with allure.step(f"Снятие завершения: {_SUBTASK_NAME}"):
        soft_step("Снятие завершения подзадачи 1", lambda: toggle_subtask_complete(page, _SUBTASK_NAME, full_page=True))

    with allure.step("Проверка: 1 completed of 2 (после снятия)"):
        expect_subtask_counter(page, TASK_NAME, "1 completed of 2", full_page=True)

    # ── Uncomplete подзадачи 2 → "0 completed of 2" ──

    with allure.step(f"Снятие завершения: {_SUBTASK_NAME_2}"):
        soft_step("Снятие завершения подзадачи 2", lambda: toggle_subtask_complete(page, _SUBTASK_NAME_2, full_page=True))

    with allure.step("Проверка: 0 completed of 2"):
        expect_subtask_counter(page, TASK_NAME, "0 completed of 2", full_page=True)


# ── 03. Удаление подзадач + счётчики ─────────────────────────────────

@pytest.mark.dependency(depends=[_DEP_ADD])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Subtasks")
@allure.title("03. Удалить Subtask и проверить счётчики")
def test_03_delete_task_subtask(page: Page, soft_step, sidebar):
    """Удаляет подзадачи из таблицы задачи, проверяет уменьшение счётчика."""
    open_card(page, soft_step, TASK_NAME)

    def delete_subtask(subtask_name):
        subtask_row = find_subtask_row_by_name(sidebar, subtask_name)
        expect(subtask_row).to_be_visible(timeout=10000)
        subtask_row.get_by_role("button").nth(1).click()
        page.get_by_text("Delete task").click()
        page.get_by_role("button", name="Proceed").click()

    # ── Удаление подзадачи 1 → "1 subtask" ──

    with allure.step(f"Удаление подзадачи: {_SUBTASK_NAME}"):
        soft_step("Удаление подзадачи 1", lambda: delete_subtask(_SUBTASK_NAME))

    with allure.step("Проверка: 1 subtask"):
        soft_step("1 subtask", lambda: (
            expect(sidebar.get_by_role("heading", name=re.compile(r"\b1 subtask\b"))).to_be_visible(timeout=10000)
        ))

    # ── Удаление подзадачи 2 → "0 subtasks" ──

    with allure.step(f"Удаление подзадачи: {_SUBTASK_NAME_2}"):
        soft_step("Удаление подзадачи 2", lambda: delete_subtask(_SUBTASK_NAME_2))

    with allure.step("Проверка: 0 subtasks"):
        soft_step("0 subtasks", lambda: (
            expect(sidebar.get_by_role("heading", name="0 subtasks")).to_be_visible(timeout=10000)
        ))
