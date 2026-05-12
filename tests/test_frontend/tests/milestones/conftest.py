import re

import allure
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.tests.tasks.conftest import open_sidebar_menu


def create_milestone_on_board(page: Page, milestone_name: str):
    """Открывает вкладку Milestones на борде и создаёт новый майлстоун."""
    page.goto(settings.AUTOTEST_BOARD_URL)
    expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=25000)
    page.get_by_role("link", name="Milestones").click()

    add_btn = page.get_by_text("Add new Milestone")
    expect(add_btn).to_be_visible(timeout=5000)
    add_btn.click()
    expect(page.get_by_role("textbox", name="Enter name...")).to_be_visible(timeout=5000)
    page.get_by_role("textbox", name="Enter name...").fill(milestone_name)
    page.keyboard.press("Enter")

    expect(page.get_by_role("heading", name=milestone_name)).to_be_visible(timeout=10000)


def open_milestone(page: Page, milestone_name: str):
    """Открывает вкладку Milestones и кликает по майлстоуну."""
    page.goto(settings.AUTOTEST_BOARD_URL)
    expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=25000)
    page.get_by_role("link", name="Milestones").click()

    milestone = page.get_by_text(milestone_name).first
    expect(milestone).to_be_visible(timeout=5000)
    milestone.click()
    expect(page.get_by_role("heading", name=milestone_name)).to_be_visible(timeout=10000)


def add_task_to_milestone(page: Page, task_name: str):
    """Добавляет задачу в открытый майлстоун."""
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    task_input = sidebar.get_by_role("textbox", name="Enter task name")
    expect(task_input).to_be_visible(timeout=5000)
    task_input.click()
    task_input.fill(task_name)
    page.keyboard.press("Enter")
    expect(
        sidebar.get_by_role("button")
        .filter(has_text=re.compile(r"[A-Z]+-\d+"))
        .filter(has_text=task_name)
    ).to_be_visible(timeout=10000)


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
    tasks = page.get_by_role("button").filter(has_text=re.compile(r"[A-Z]+-\d+"))
    while tasks.first.is_visible(timeout=3000):
        tasks.first.get_by_role("button").nth(1).click()
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


def cleanup_milestones(page: Page, keep_names: list[str] | None = None):
    """Архивирует все майлстоуны на борде кроме указанных в keep_names. Best effort."""
    keep = set(keep_names or [])

    with allure.step(f"Cleanup: архивация майлстоунов (кроме {keep or 'никого'})"):
        page.goto(settings.AUTOTEST_BOARD_URL)
        expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=25000)
        page.get_by_role("link", name="Milestones").click()
        page.wait_for_timeout(2000)

        def _archive_visible():
            """Архивирует видимые в DOM майлстоуны. Возвращает кол-во архивированных."""
            count = 0
            for _ in range(20):
                rows = page.locator('[class*="List-module_VirtualItem"]')
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

        # Если что-то архивировали — reload и второй проход (виртуальный скролл)
        if archived > 0:
            page.reload()
            expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=25000)
            page.get_by_role("link", name="Milestones").click()
            page.wait_for_timeout(2000)
            archived += _archive_visible()
