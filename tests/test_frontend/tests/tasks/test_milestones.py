import re
from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.tests.tasks.conftest import open_card, open_sidebar_menu, _wait_board_ready

pytestmark = [pytest.mark.frontend]

_DEP_TASK = "test_01_create_task"
_DEP_FILL = "test_02_fill_fields"
_DEP_CONVERT = "test_03_convert_to_milestone"

_TS = datetime.now().strftime("%H%M%S")
_TASK_NAME = f"milestone_{_TS}"
_SUBTASK_NAME = f"Sub milestone {_TS}"
_DESCRIPTION = f"Milestone desc {_TS}"
_COMMENT = f"Milestone comment {_TS}"
_DATE = "10.08.2030"
_MILESTONE_NAME = "Test milestone"


# ── 01. Создание задачи ──────────────────────────────────────────────


@pytest.mark.dependency(name=_DEP_TASK)
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("01. Create task for conversion")
def test_01_create_task(page: Page, soft_step):
    """Создаёт задачу, которая будет конвертирована в майлстоун."""
    with allure.step("Открытие борды"):
        soft_step("Открытие борды", lambda: (
            page.goto(settings.AUTOTEST_BOARD_URL),
            expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=15000),
        ))

    def create_task():
        page.get_by_role("button", name="Add task").first.click()
        expect(page.get_by_role("textbox", name="Task name...")).to_be_visible(timeout=5000)
        page.get_by_role("textbox", name="Task name...").fill(_TASK_NAME)
        page.locator("#board-card-create").get_by_role("button", name="Add task").click()

    with allure.step(f"Создание задачи: {_TASK_NAME}"):
        soft_step("Создание задачи", create_task)

    def verify_card():
        task_card = page.get_by_role("button").filter(
            has_text=re.compile(r"[A-Z]+-\d+")
        ).filter(has_text=_TASK_NAME)
        expect(task_card).to_be_visible(timeout=10000)

    with allure.step("Проверка: карточка видна на борде"):
        soft_step("Карточка на борде", verify_card)


# ── 02. Заполнение всех полей задачи ─────────────────────────────────


@pytest.mark.dependency(name=_DEP_FILL, depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("02. Fill all task fields before conversion")
def test_02_fill_fields(page: Page, soft_step):
    """Заполняет все поля задачи перед конвертацией.
    Переносятся: название, описание, дата, подзадача, комментарий.
    Теряются: приоритет, исполнитель, тип, майлстоун."""
    open_card(page, soft_step, _TASK_NAME)

    # ── Поля, которые переносятся ──

    # Описание
    def set_description():
        desc_editor = page.locator('[id^="editor-content-"]')
        desc_editor.get_by_role("paragraph").click()
        desc_editor.locator('[contenteditable="true"]').fill(_DESCRIPTION)
        expect(desc_editor).to_contain_text(_DESCRIPTION, timeout=5000)
        page.keyboard.press("Escape")

    with allure.step(f"Описание: {_DESCRIPTION}"):
        soft_step("Описание", set_description)

    # Дата
    def set_date():
        page.get_by_role("button", name="Dates No dates set").click()
        date_input = page.get_by_placeholder(re.compile(r"\d{2}\.\d{2}\.\d{4}")).first
        date_input.fill(_DATE)
        page.get_by_role("button", name="Apply").click()
        expect(page.get_by_role("button", name="Dates No dates set")).not_to_be_visible(timeout=5000)

    with allure.step(f"Дата: {_DATE}"):
        soft_step("Дата", set_date)

    # Подзадача
    def add_subtask():
        page.get_by_role("textbox", name="Enter subtask name").fill(_SUBTASK_NAME)
        page.keyboard.press("Enter")
        expect(page.get_by_text(_SUBTASK_NAME).first).to_be_visible(timeout=5000)

    with allure.step(f"Подзадача: {_SUBTASK_NAME}"):
        soft_step("Подзадача", add_subtask)

    # Комментарий
    def add_comment():
        toolbar = page.locator('[class*="CommentToolbar-module"]').first
        toolbar.scroll_into_view_if_needed()
        comment_editor = toolbar.locator('xpath=ancestor::div[contains(@class, "Comment")]').locator(".tiptap")
        comment_editor.click()
        comment_editor.fill(_COMMENT)
        send_btn = page.locator('[class*="CommentToolbar-module_Right"]').get_by_role("button").last
        expect(send_btn).to_be_enabled(timeout=5000)
        send_btn.click()

    with allure.step(f"Комментарий: {_COMMENT}"):
        soft_step("Комментарий", add_comment)

    # ── Поля, которые теряются при конвертации ──

    # Приоритет
    def set_priority():
        page.get_by_role("button", name="Priority Select priority").click()
        page.get_by_text("Medium").click()
        expect(page.get_by_role("button", name=re.compile(r"Priority.*Medium"))).to_be_visible(timeout=5000)

    with allure.step("Приоритет: Medium"):
        soft_step("Приоритет", set_priority)

    # Исполнитель
    def set_assignee():
        page.get_by_role("button", name="Assign Not assigned").click()
        page.locator('.szh-menu-container [class*="SelectFlySearch-module_ItemText"]').first.click()
        page.locator('[class*="FlyBlock-module_Overlay"]').click()
        expect(page.get_by_role("button", name=re.compile(r"Assign\s+\S"))).to_be_visible(timeout=5000)

    with allure.step("Исполнитель"):
        soft_step("Исполнитель", set_assignee)

    # Тип
    def set_type():
        page.get_by_role("button", name="Types Select type").click()
        page.get_by_role("menuitem", name="Green").click()
        expect(page.get_by_role("button", name=re.compile(r"Types.*Green"))).to_be_visible(timeout=5000)

    with allure.step("Тип: Green"):
        soft_step("Тип", set_type)

    # Майлстоун
    def set_milestone():
        page.get_by_role("button", name="Milestones Select milestones").click()
        page.get_by_role("textbox", name="Type to search...").fill(_MILESTONE_NAME)
        page.get_by_role("menuitem", name=_MILESTONE_NAME).click()
        expect(page.get_by_role("button", name=re.compile(rf"Milestones.*{_MILESTONE_NAME}"))).to_be_visible(timeout=5000)

    with allure.step(f"Майлстоун: {_MILESTONE_NAME}"):
        soft_step("Майлстоун", set_milestone)



# ── 03. Конвертация в майлстоун ──────────────────────────────────────


@pytest.mark.dependency(name=_DEP_CONVERT, depends=[_DEP_FILL])
@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("03. Convert task to milestone")
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
                has_text=re.compile(r"[A-Z]+-\d+")
            ).filter(has_text=_TASK_NAME)
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
@allure.suite("Milestones")
@allure.title("04. Verify milestone fields via subtask")
def test_04_verify_fields(page: Page, soft_step):
    """Открывает сабтаску на борде, проверяет milestone field,
    переходит на майлстоун по бейджу и проверяет перенос полей."""
    open_card(page, soft_step, _SUBTASK_NAME)

    # ── Проверка milestone field на сабтаске ──

    with allure.step("Milestone field на сабтаске"):
        soft_step("Milestone field", lambda: (
            expect(page.get_by_role("button", name=re.compile(rf"Milestones.*{_TASK_NAME}"))).to_be_visible(timeout=5000)
        ))

    # ── Переход на майлстоун по иконке-ссылке (hard fail) ──

    with allure.step("Переход на майлстоун по иконке-ссылке"):
        milestone_field = page.get_by_role("button", name=re.compile(rf"Milestones.*{_TASK_NAME}"))
        milestone_field.locator('i[class*="Badge-module_Icon"]').click()
        expect(page.get_by_role("heading", name=_TASK_NAME)).to_be_visible(timeout=10000)

    # ── Проверка полей майлстоуна (перенеслись) ──

    with allure.step("Проверка описания"):
        soft_step("Описание", lambda: (
            expect(page.locator(".tiptap").first).to_contain_text(_DESCRIPTION, timeout=5000)
        ))

    with allure.step("Проверка даты"):
        soft_step("Дата", lambda: (
            expect(page.get_by_role("button", name=re.compile(r"Dates.*2030"))).to_be_visible(timeout=5000)
        ))

    with allure.step("Проверка подзадачи"):
        soft_step("Подзадача", lambda: (
            expect(page.get_by_text(_SUBTASK_NAME).first).to_be_visible(timeout=5000)
        ))

    with allure.step("Проверка комментария"):
        soft_step("Комментарий", lambda: (
            expect(page.get_by_text(_COMMENT)).to_be_visible(timeout=5000)
        ))

    # ── Поля, которые должны были потеряться ──

    with allure.step("Приоритет отсутствует"):
        soft_step("Приоритет потерян", lambda: (
            expect(page.get_by_role("button", name=re.compile(r"Priority.*Medium"))).not_to_be_visible(timeout=3000)
        ))

    with allure.step("Исполнитель отсутствует"):
        soft_step("Исполнитель потерян", lambda: (
            expect(page.get_by_role("button", name=re.compile(r"Assign\s+\S"))).not_to_be_visible(timeout=3000)
        ))

    with allure.step("Тип отсутствует"):
        soft_step("Тип потерян", lambda: (
            expect(page.get_by_role("button", name=re.compile(r"Types.*Green"))).not_to_be_visible(timeout=3000)
        ))



# ── Cleanup: архивация ───────────────────────────────────────────


@allure.parent_suite("Frontend")
@allure.suite("Milestones")
@allure.title("99. Cleanup: delete subtask and archive milestone")
def test_cleanup(page: Page, soft_step, cleanup_task):
    """Архивирует майлстоун и удаляет сабтаску для очистки борды."""
    # cleanup_task удалит сабтаску (и другие карточки с _TS) после теста
    cleanup_task["ts"] = _TS

    # Архивация майлстоуна через вкладку Milestones
    try:
        with allure.step("Открытие вкладки Milestones"):
            page.goto(settings.AUTOTEST_BOARD_URL)
            expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=15000)
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
