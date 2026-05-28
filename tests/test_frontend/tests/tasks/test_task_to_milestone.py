import re
from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Board
from tests.test_frontend.tests.tasks.conftest import (
    create_task_on_board, open_card, open_sidebar_menu, _wait_board_ready,
    add_comment, fill_description, find_subtask_row_by_name, _scroll_to_subtasks,
    set_date as _set_date, future_date,
)

pytestmark = [pytest.mark.frontend]

_DEP_TASK = "test_01_create_task"
_DEP_FILL = "test_02_fill_fields"
_DEP_CONVERT = "test_03_convert_to_milestone"

_TS = datetime.now().strftime("%H%M%S")
_TASK_NAME = f"ConvTask {_TS}"
_SUBTASK_NAME = f"ConvSub {_TS}"
_SUB_SUBTASK_NAME = f"ConvSubSub {_TS}"
_DESCRIPTION = f"Milestone desc {_TS}"
_COMMENT = f"Milestone comment {_TS}"
_DATE = future_date(10)
_MILESTONE_NAME = "Test milestone"


# ── Auto-debug: setup/cleanup при запуске отдельного теста из IDE ──


def _debug_create(page):
    create_task_on_board(page, _TASK_NAME)


def _debug_teardown(page):
    from tests.test_frontend.conftest import cleanup_board
    from tests.test_frontend.tests.milestones.conftest import cleanup_milestones
    cleanup_milestones(page, keep_names=["Test milestone"])
    cleanup_board(page)


def _setup_fill(page):
    """Заполняет поля задачи для тестов, зависящих от test_02."""
    from tests.test_frontend.tests.tasks.conftest import add_subtask, fill_description
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    card = page.get_by_role("button").filter(
        has_text=re.compile(r"[A-Z]+-\d+")
    ).filter(has_text=_TASK_NAME).first
    expect(card).to_be_visible(timeout=10000)
    card.click()
    expect(sidebar.get_by_role("heading", name=_TASK_NAME)).to_be_visible(timeout=10000)
    fill_description(page, _DESCRIPTION)
    add_subtask(page, _SUBTASK_NAME)
    # Подподзадача
    find_subtask_row_by_name(sidebar, _SUBTASK_NAME).first.click()
    expect(sidebar.get_by_role("heading", name=_SUBTASK_NAME)).to_be_visible(timeout=10000)
    sidebar.get_by_role("textbox", name="Enter subtask name").fill(_SUB_SUBTASK_NAME)
    page.keyboard.press("Enter")
    expect(find_subtask_row_by_name(sidebar, _SUB_SUBTASK_NAME)).to_be_visible(timeout=5000)


def _setup_convert(page):
    """Заполняет поля + конвертирует задачу для тестов, зависящих от test_03."""
    from tests.test_frontend.tests.tasks.conftest import open_card, open_sidebar_menu, _wait_board_ready
    _setup_fill(page)
    # Возвращаемся на родительскую задачу и конвертируем
    open_card(page, lambda name, fn: fn(), _TASK_NAME)
    open_sidebar_menu(page)
    page.get_by_text("Convert to Milestone").click()
    page.get_by_role("button", name="Convert").click()
    expect(page.get_by_text("Task successfully converted to Milestone")).to_be_visible(timeout=10000)


_debug_extra_setup = {
    "test_03_convert_to_milestone": _setup_fill,
    "test_04_verify_fields": _setup_convert,
    "test_05_subtasks_kept": _setup_convert,
}


# ── 01. Создание задачи ──────────────────────────────────────────────


@pytest.mark.dependency(name=_DEP_TASK)
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Convert to Milestone")
@allure.title("01. Создать Task для конвертации")
def test_01_create_task(page: Page, soft_step):
    """Создаёт задачу, которая будет конвертирована в майлстоун."""
    with allure.step(f"Создание задачи: {_TASK_NAME}"):
        soft_step("Создание задачи", lambda: create_task_on_board(page, _TASK_NAME))


# ── 02. Заполнение всех полей задачи ─────────────────────────────────


@pytest.mark.dependency(name=_DEP_FILL, depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Convert to Milestone")
@allure.title("02. Заполнить все поля Task перед конвертацией")
def test_02_fill_fields(page: Page, soft_step, sidebar):
    """Заполняет все поля задачи перед конвертацией.
    Переносятся: название, описание, дата, подзадача, комментарий.
    Теряются: приоритет, исполнитель, тип, майлстоун."""
    open_card(page, soft_step, _TASK_NAME)

    # ── Поля, которые переносятся ──

    # Описание
    with allure.step(f"Описание: {_DESCRIPTION}"):
        soft_step("Описание", lambda: fill_description(page, _DESCRIPTION))

    # Дата
    with allure.step(f"Дата: {_DATE}"):
        soft_step("Дата", lambda: _set_date(page, _DATE))

    # Подзадача
    def add_subtask():
        _scroll_to_subtasks(sidebar)
        textbox = sidebar.get_by_role("textbox", name="Enter subtask name")
        expect(textbox).to_be_visible(timeout=5000)
        textbox.fill(_SUBTASK_NAME)
        page.keyboard.press("Enter")
        expect(find_subtask_row_by_name(sidebar, _SUBTASK_NAME)).to_be_visible(timeout=10000)

    with allure.step(f"Подзадача: {_SUBTASK_NAME}"):
        soft_step("Подзадача", add_subtask)

    # Комментарий
    with allure.step(f"Комментарий: {_COMMENT}"):
        soft_step("Комментарий", lambda: add_comment(page, _COMMENT))

    # ── Поля, которые теряются при конвертации ──

    # Приоритет
    def set_priority():
        sidebar.get_by_role("button", name="Priority Select priority").click()
        page.get_by_text("Medium").click()
        expect(sidebar.get_by_role("button", name=re.compile(r"Priority.*Medium"))).to_be_visible(timeout=5000)

    with allure.step("Приоритет: Medium"):
        soft_step("Приоритет", set_priority)

    # Исполнитель
    def set_assignee():
        sidebar.get_by_role("button", name="Assign Not assigned").click()
        page.locator('.szh-menu-container [class*="SelectFlySearch-module_ItemText"]').first.click()
        page.locator('[class*="FlyBlock-module_Overlay"]').click()
        expect(sidebar.get_by_role("button", name=re.compile(r"Assign\s+\S"))).to_be_visible(timeout=5000)

    with allure.step("Исполнитель"):
        soft_step("Исполнитель", set_assignee)

    # Тип
    def set_type():
        sidebar.get_by_role("button", name="Types Select type").click()
        page.get_by_role("menuitem", name="Green").click()
        expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Green"))).to_be_visible(timeout=5000)

    with allure.step("Тип: Green"):
        soft_step("Тип", set_type)

    # Майлстоун
    def set_milestone():
        sidebar.get_by_role("button", name="Milestones Select milestones").click()
        page.get_by_role("textbox", name="Type to search...").fill(_MILESTONE_NAME)
        expect(page.get_by_role("menuitem", name=_MILESTONE_NAME)).to_be_visible(timeout=5000)
        page.get_by_role("menuitem", name=_MILESTONE_NAME).click()
        expect(sidebar.get_by_role("button", name=re.compile(rf"Milestones.*{_MILESTONE_NAME}"))).to_be_visible(timeout=5000)

    with allure.step(f"Майлстоун: {_MILESTONE_NAME}"):
        soft_step("Майлстоун", set_milestone)

    # ── Подподзадача (последний шаг — уходим в сайдбар подзадачи) ──

    def add_sub_sub_task():
        _scroll_to_subtasks(sidebar)
        find_subtask_row_by_name(sidebar, _SUBTASK_NAME).first.click()
        expect(sidebar.get_by_role("heading", name=_SUBTASK_NAME)).to_be_visible(timeout=10000)
        _scroll_to_subtasks(sidebar)
        sidebar.get_by_role("textbox", name="Enter subtask name").fill(_SUB_SUBTASK_NAME)
        page.keyboard.press("Enter")
        expect(find_subtask_row_by_name(sidebar, _SUB_SUBTASK_NAME)).to_be_visible(timeout=10000)

    with allure.step(f"Подподзадача: {_SUB_SUBTASK_NAME}"):
        soft_step("Подподзадача", add_sub_sub_task)


# ── 03. Конвертация в майлстоун ──────────────────────────────────────


@pytest.mark.dependency(name=_DEP_CONVERT, depends=[_DEP_FILL])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Convert to Milestone")
@allure.title("03. Конвертировать Task в Milestone")
def test_03_convert_to_milestone(page: Page, soft_step):
    """Конвертирует задачу в майлстоун через меню сайдбара."""
    open_card(page, soft_step, _TASK_NAME)

    def convert():
        open_sidebar_menu(page)
        page.get_by_text("Convert to Milestone").click()
        page.get_by_role("button", name="Convert").click()

    with allure.step("Конвертация в майлстоун"):
        soft_step("Конвертация", convert)

    with allure.step("Тост: Task successfully converted to Milestone"):
        soft_step("Тост конвертации", lambda: (
            expect(page.get_by_text("Task successfully converted to Milestone")).to_be_visible(timeout=10000)
        ))

    def verify_card_gone():
        page.goto(settings.AUTOTEST_BOARD_URL)
        _wait_board_ready(page)
        for attempt in range(4):
            task_card = page.get_by_role("button").filter(
                has_text=re.compile(rf"·\s*{re.escape(_TASK_NAME)}")
            )
            if not task_card.is_visible():
                break
            if attempt < 3:
                page.wait_for_timeout(2000)
                page.reload()
                _wait_board_ready(page)
        expect(task_card).not_to_be_visible(timeout=5000)

    with allure.step("Проверка: карточка задачи исчезла с борды"):
        soft_step("Карточка исчезла", verify_card_gone)


# ── 04. Проверка переноса полей ──────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CONVERT])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Convert to Milestone")
@allure.title("04. Проверить поля Milestone через Subtask")
def test_04_verify_fields(page: Page, soft_step, sidebar):
    """Открывает сабтаску на борде, проверяет milestone field,
    переходит на майлстоун по бейджу и проверяет перенос полей."""
    open_card(page, soft_step, _SUBTASK_NAME)

    # ── Проверка milestone field на сабтаске ──

    with allure.step("Milestone field на сабтаске"):
        soft_step("Milestone field", lambda: (
            expect(sidebar.get_by_role("button", name=re.compile(rf"Milestones.*{_TASK_NAME}"))).to_be_visible(timeout=5000)
        ))

    # ── Переход на майлстоун по иконке-ссылке (hard fail) ──

    with allure.step("Переход на майлстоун по иконке-ссылке"):
        milestone_field = sidebar.get_by_role("button", name=re.compile(rf"Milestones.*{_TASK_NAME}"))
        milestone_field.locator('i[class*="Badge-module_Icon"]').click()
        expect(sidebar.get_by_role("heading", name=_TASK_NAME)).to_be_visible(timeout=10000)

    # ── Проверка полей майлстоуна (перенеслись) ──

    with allure.step("Проверка описания"):
        soft_step("Описание", lambda: (
            expect(sidebar.locator('.tiptap').filter(has_text=_DESCRIPTION).first).to_be_visible(timeout=5000)
        ))

    with allure.step("Проверка даты"):
        _d = datetime.strptime(_DATE, "%d.%m.%Y")
        _expected_date = f"{_d.day} {_d.strftime('%B')} {_d.year}"
        soft_step("Дата", lambda: (
            expect(sidebar.get_by_text(_expected_date)).to_be_visible(timeout=5000)
        ))

    with allure.step("Проверка подзадачи"):
        soft_step("Подзадача", lambda: (
            expect(find_subtask_row_by_name(sidebar, _SUBTASK_NAME)).to_be_visible(timeout=5000)
        ))

    with allure.step("Проверка комментария"):
        soft_step("Комментарий", lambda: (
            expect(sidebar.get_by_text(_COMMENT)).to_be_visible(timeout=5000)
        ))

    # ── Поля, которые должны были потеряться ──

    with allure.step("Приоритет отсутствует"):
        soft_step("Приоритет потерян", lambda: (
            expect(sidebar.get_by_role("button", name=re.compile(r"Priority.*Medium"))).not_to_be_visible(timeout=3000)
        ))

    with allure.step("Исполнитель отсутствует"):
        soft_step("Исполнитель потерян", lambda: (
            expect(sidebar.get_by_role("button", name=re.compile(r"Assign\s+\S"))).not_to_be_visible(timeout=3000)
        ))

    with allure.step("Тип отсутствует"):
        soft_step("Тип потерян", lambda: (
            expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Green"))).not_to_be_visible(timeout=3000)
        ))



# ── 05. Проверка сохранения иерархии подзадач ───────────────────────


@pytest.mark.dependency(depends=[_DEP_CONVERT])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Convert to Milestone")
@allure.title("05. Subtasks сохранились после конвертации")
def test_05_subtasks_kept(page: Page, sidebar):
    """Проверяет что подзадача с вложенной подподзадачей сохранились после конвертации."""
    from tests.test_frontend.tests.milestones.conftest import open_milestone

    open_milestone(page, _TASK_NAME)

    with allure.step(f"Проверка: {_SUBTASK_NAME} видна как задача майлстоуна"):
        expect(sidebar.get_by_text(_SUBTASK_NAME).first).to_be_visible(timeout=10000)

    with allure.step(f"Открытие {_SUBTASK_NAME} и проверка подподзадачи"):
        sidebar.get_by_text(_SUBTASK_NAME).first.click()
        expect(sidebar.get_by_role("heading", name=_SUBTASK_NAME)).to_be_visible(timeout=10000)
        _scroll_to_subtasks(sidebar)
        expect(find_subtask_row_by_name(sidebar, _SUB_SUBTASK_NAME)).to_be_visible(timeout=10000)


# ── Cleanup: архивация ───────────────────────────────────────────


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Convert to Milestone")
@allure.title("99. Очистка: удалить Subtask и архивировать Milestone")
def test_cleanup(page: Page, soft_step, cleanup_task):
    """Архивирует майлстоун и удаляет сабтаску для очистки борды."""
    # cleanup_task удалит сабтаску (и другие карточки с _TS) после теста
    cleanup_task["ts"] = _TS

    # Архивация майлстоуна через вкладку Milestones
    try:
        with allure.step("Открытие вкладки Milestones"):
            page.goto(settings.AUTOTEST_BOARD_URL)
            expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=25000)
            page.get_by_role("link", name="Milestones").click()

        with allure.step(f"Поиск майлстоуна '{_TASK_NAME}'"):
            milestone = page.get_by_text(_TASK_NAME).first
            expect(milestone).to_be_visible(timeout=5000)
            milestone.click()

        with allure.step("Архивация майлстоуна"):
            open_sidebar_menu(page)
            page.get_by_text("Archive milestone").click()
            page.get_by_role("button", name="Yes").click()

        with allure.step("Тост: Milestone archived"):
            expect(page.get_by_text("Milestone archived")).to_be_visible(timeout=5000)
    except Exception:
        pass
