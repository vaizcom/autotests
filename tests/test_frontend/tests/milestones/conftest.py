import re

import allure
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.tests.tasks.conftest import open_sidebar_menu


def create_milestone_on_board(page: Page, milestone_name: str):
    """Открывает вкладку Milestones на борде и создаёт новый майлстоун."""
    page.goto(settings.AUTOTEST_BOARD_URL)
    expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=15000)
    page.get_by_role("link", name="Milestones").click()

    page.get_by_text("Add new Milestone").click()
    expect(page.get_by_role("textbox", name="Enter name...")).to_be_visible(timeout=5000)
    page.get_by_role("textbox", name="Enter name...").fill(milestone_name)
    page.keyboard.press("Enter")

    expect(page.get_by_role("heading", name=milestone_name)).to_be_visible(timeout=10000)


def open_milestone(page: Page, milestone_name: str):
    """Открывает вкладку Milestones и кликает по майлстоуну."""
    page.goto(settings.AUTOTEST_BOARD_URL)
    expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=15000)
    page.get_by_role("link", name="Milestones").click()

    milestone = page.get_by_text(milestone_name).first
    expect(milestone).to_be_visible(timeout=5000)
    milestone.click()
    expect(page.get_by_role("heading", name=milestone_name)).to_be_visible(timeout=10000)


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
