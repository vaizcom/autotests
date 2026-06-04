import re

import allure
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Board
from tests.test_frontend.tests.tasks.conftest import open_sidebar_menu


def create_milestone_on_board(page: Page, milestone_name: str):
    """Открывает вкладку Milestones на борде и создаёт новый майлстоун."""
    page.goto(settings.AUTOTEST_BOARD_URL)
    expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=25000)
    page.get_by_role("link", name="Milestones").click()

    name_input = page.get_by_placeholder("Enter milestone name")
    expect(name_input).to_be_visible(timeout=5000)
    name_input.fill(milestone_name)
    page.keyboard.press("Enter")

    expect(page.get_by_role("heading", name=milestone_name)).to_be_visible(timeout=10000)


def open_milestone(page: Page, milestone_name: str):
    """Открывает вкладку Milestones и кликает по майлстоуну."""
    page.goto(settings.AUTOTEST_BOARD_URL)
    expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=25000)
    page.get_by_role("link", name="Milestones").click()

    milestone = page.get_by_text(milestone_name).first
    expect(milestone).to_be_visible(timeout=5000)
    milestone.click()
    expect(page.get_by_role("heading", name=milestone_name)).to_be_visible(timeout=10000)


def add_task_to_milestone(page: Page, task_name: str):
    """Добавляет задачу в открытый майлстоун."""
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    task_input = sidebar.get_by_placeholder("Enter task name")
    expect(task_input).to_be_visible(timeout=10000)
    task_input.click()
    task_input.fill(task_name)
    create_option = page.get_by_text("Create task")
    expect(create_option).to_be_visible(timeout=5000)
    create_option.click()
    page.wait_for_timeout(2000)
    expect(sidebar.get_by_text(task_name).first).to_be_visible(timeout=10000)


def wait_for_task_rows(page: Page, milestone_name: str):
    """Ждёт загрузки строк задач в таблице майлстоуна с ретраями и reload."""
    task_rows = page.get_by_role("button").filter(has_text=re.compile(r"[A-Z]+-\d+"))
    for attempt in range(4):
        if task_rows.first.is_visible():
            return
        if attempt < 3:
            page.wait_for_timeout(2000)
            page.reload()
            expect(page.get_by_role("heading", name=milestone_name)).to_be_visible(timeout=10000)
    expect(task_rows.first).to_be_visible(timeout=5000)


def delete_milestone_tasks(page: Page):
    """Удаляет все задачи внутри открытого майлстоуна. Best effort."""
    rows = page.get_by_role("button").filter(has_text=re.compile(r"[A-Z]+-\d+"))
    while rows.first.is_visible(timeout=3000):
        rows.first.get_by_role("button").last.click()
        page.get_by_text("Delete task").click()
        page.get_by_role("button", name="Proceed").click()
        page.wait_for_timeout(1000)


def archive_milestone(page: Page, milestone_name: str):
    """Удаляет задачи и архивирует майлстоун. Best effort."""
    try:
        with allure.step(f"Удаление задач майлстоуна '{milestone_name}'"):
            open_milestone(page, milestone_name)
            delete_milestone_tasks(page)
        with allure.step(f"Архивация майлстоуна '{milestone_name}'"):
            open_sidebar_menu(page)
            page.get_by_text("Archive milestone").click()
            page.get_by_role("button", name="Yes").click()
            expect(page.get_by_text("Milestone archived")).to_be_visible(timeout=5000)
    except Exception:
        pass


def cleanup_milestones(page: Page, keep_names=None):
    """Архивирует все майлстоуны на борде кроме указанных в keep_names. Best effort."""
    keep = set(keep_names or [])

    with allure.step(f"Cleanup: архивация майлстоунов (кроме {keep or 'никого'})"):
        page.goto(settings.AUTOTEST_BOARD_URL)
        expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=25000)
        page.get_by_role("link", name="Milestones").click()
        page.wait_for_timeout(2000)

        _ROW_SELECTOR = '[class*="MilestoneBoard-module_Row"]'

        def _check_stale_selector():
            """Проверяет, что селектор строк находит элементы. Иначе — скриншот + warning."""
            if page.locator(_ROW_SELECTOR).count() > 0:
                return
            # Страница загружена (инпут виден), но строки не найдены — селектор устарел
            if page.get_by_placeholder("Enter milestone name").is_visible(timeout=3000):
                allure.attach(
                    page.screenshot(),
                    name="⚠️ cleanup: селектор строк не находит элементов",
                    attachment_type=allure.attachment_type.PNG,
                )
                print(
                    f"⚠️ cleanup_milestones: селектор '{_ROW_SELECTOR}' не нашёл строк, "
                    f"но страница Milestones загружена — возможно CSS-класс изменился"
                )

        def _archive_visible():
            """Архивирует видимые в DOM майлстоуны. Возвращает кол-во архивированных."""
            _check_stale_selector()
            count = 0
            for _ in range(20):
                rows = page.locator(_ROW_SELECTOR)
                found = False

                for i in range(rows.count()):
                    row = rows.nth(i)
                    title = row.locator('[class*="List-module_Title"]')
                    if title.count() == 0:
                        continue
                    name = title.first.inner_text(timeout=3000).split("\n")[0].strip()
                    if name in keep:
                        continue

                    found = True
                    try:
                        menu_btn = row.locator('[class*="HoverShow"] button').first
                        row.hover()
                        expect(menu_btn).to_be_visible(timeout=3000)
                        menu_btn.click()
                        page.get_by_text("Archive milestone").click()
                        page.get_by_role("button", name="Yes").click()
                        expect(page.get_by_text("Milestone archived")).to_be_visible(timeout=5000)
                        page.wait_for_timeout(1500)
                        count += 1
                    except Exception:
                        # Не удалось — закрываем меню/диалог если открыт и пробуем следующий
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(500)
                    break

                if not found:
                    break
            return count

        # Первый проход
        archived = _archive_visible()

        # Если что-то архивировали — заново открыть вкладку и второй проход (виртуальный скролл)
        if archived > 0:
            page.goto(settings.AUTOTEST_BOARD_URL)
            expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=25000)
            page.get_by_role("link", name="Milestones").click()
            page.wait_for_timeout(2000)
            archived += _archive_visible()
