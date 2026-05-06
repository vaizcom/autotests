import re
from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.tests.tasks.conftest import open_card, create_task_on_board

pytestmark = [pytest.mark.frontend]

# test_01 — создаёт задачу, остальные зависят от неё.
# При падении test_01 зависимые тесты будут SKIP, а не FAIL.
_DEP_TASK = "test_01_create_task"

_TS = datetime.now().strftime("%H%M%S")
_TASK_NAME = f"autotest_{_TS}"
_SUBTASK_NAME = f"Test subtask {_TS}"
_DESCRIPTION = f"Test description {_TS}"
_COMMENT = f"Test comment {_TS}"
_MILESTONE_NAME = "Test milestone"
_BLOCKER_NAME = f"Blocker task {_TS}"
_BLOCKING_NAME = f"Blocking task {_TS}"
_CUSTOM_TEXT_VALUE = f"Test value {_TS}"



@pytest.mark.dependency(name=_DEP_TASK)
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.title("01. Create task on board")
def test_01_create_task(page: Page, soft_step):
    """Создаёт новую задачу на борде и проверяет что карточка появилась."""
    with allure.step(f"Создание задачи: {_TASK_NAME}"):
        soft_step("Создание задачи", lambda: create_task_on_board(page, _TASK_NAME))


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
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
@allure.title("05. Fill description")
def test_05_description(page: Page, soft_step):
    """Заполняет описание задачи."""
    open_card(page, soft_step, _TASK_NAME)

    def set_description():
        page.locator('[id^="editor-content-"]').get_by_role("paragraph").click()
        page.locator(".tiptap").first.fill(_DESCRIPTION)
        expect(page.locator(".tiptap").first).to_contain_text(_DESCRIPTION, timeout=5000)

    with allure.step(f"Ввод описания: {_DESCRIPTION}"):
        soft_step("Описание", set_description)


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.title("06. Add subtask")
def test_06_subtask(page: Page, soft_step):
    """Добавляет подзадачу к задаче."""
    open_card(page, soft_step, _TASK_NAME)

    def add_subtask():
        page.get_by_role("textbox", name="Enter subtask name").fill(_SUBTASK_NAME)
        page.keyboard.press("Enter")
        expect(page.get_by_text(_SUBTASK_NAME)).to_be_visible(timeout=5000)

    with allure.step(f"Создание подзадачи: {_SUBTASK_NAME}"):
        soft_step("Подзадача", add_subtask)


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.title("07. Add milestone")
def test_07_milestone(page: Page, soft_step):
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
@allure.title("08. Set date")
def test_08_date(page: Page, soft_step):
    """Устанавливает дату задачи."""
    open_card(page, soft_step, _TASK_NAME)

    def add_date():
        page.get_by_role("button", name="Dates No dates set").click()
        date_input = page.get_by_placeholder(re.compile(r"\d{2}\.\d{2}\.\d{4}")).first
        date_input.fill("10.08.2030")
        page.get_by_role("button", name="Apply").click()
        expect(page.get_by_role("button", name="Dates No dates set")).not_to_be_visible(timeout=5000)

    with allure.step("Установка даты 10.08.2030"):
        soft_step("Дата", add_date)


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.title("09. Add blocker and blocking")
def test_09_blockers(page: Page, soft_step):
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
@allure.title("10. Fill custom text field")
def test_10_custom_field(page: Page, soft_step):
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
@allure.title("11. Add comment")
def test_11_comment(page: Page, soft_step):
    """Добавляет комментарий к задаче."""
    open_card(page, soft_step, _TASK_NAME)

    def add_comment():
        # Комментарий — tiptap-редактор рядом с CommentToolbar (не путать с полем подзадачи)
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


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.title("12. Complete task")
def test_12_complete(page: Page, soft_step):
    """Отмечает задачу как выполненную (Complete). Последний перед cleanup, чтобы не скрыть карточку."""
    open_card(page, soft_step, _TASK_NAME)

    with allure.step("Клик по чекбоксу Complete"):
        soft_step("Complete", lambda: page.locator('[class*="_Check_"]').first.click())


@pytest.mark.dependency(depends=[_DEP_TASK])
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.title("99. Cleanup: delete test tasks")
def test_99_cleanup(page: Page, cleanup_task):
    """Удаляет все карточки с таймстемпом теста с борды."""
    cleanup_task["ts"] = _TS
