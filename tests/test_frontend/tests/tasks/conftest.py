import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings


def _wait_board_ready(page: Page):
    """Ждёт полной загрузки борды: кнопка Add task + карточки или пустая колонка."""
    expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=15000)
    # Борда загружена, если видна хотя бы одна карточка или счётчик "0 tasks"
    loaded = page.get_by_role("button").filter(has_text=re.compile(r"[A-Z]+-\d+")).first.or_(
        page.get_by_text(re.compile(r"\d+ tasks?")).first
    ).first
    expect(loaded).to_be_visible(timeout=15000)


def wait_for_card(page: Page, card_name: str, go_to_board: bool = True):
    """Ждёт появления карточки на борде с ретраями и reload."""
    if go_to_board:
        page.goto(settings.AUTOTEST_BOARD_URL)
    _wait_board_ready(page)

    for attempt in range(4):
        card = page.get_by_role("button").filter(
            has_text=re.compile(r"[A-Z]+-\d+")
        ).filter(has_text=card_name)
        if card.is_visible():
            return card
        if attempt < 3:
            page.wait_for_timeout(2000)
            page.reload()
            _wait_board_ready(page)
    raise AssertionError(f"Карточка '{card_name}' не найдена на борде после 4 попыток")


def open_card(page: Page, soft_step, card_name: str):
    """Открывает борду и кликает по карточке с заданным именем, открывая сайдбар."""
    with allure.step(f"Открытие борды и поиск карточки '{card_name}'"):
        wait_for_card(page, card_name)

    def _open_sidebar():
        task_card = page.get_by_role("button").filter(
            has_text=re.compile(r"[A-Z]+-\d+")
        ).filter(has_text=card_name)
        expect(task_card).to_be_visible(timeout=15000)
        task_card.click()
        expect(page.get_by_role("heading", name=card_name)).to_be_visible(timeout=10000)

    with allure.step(f"Открытие карточки '{card_name}' в сайдбаре"):
        soft_step(f"Открытие '{card_name}' в сайдбаре", _open_sidebar)


def create_task_on_board(page: Page, task_name: str):
    """Открывает борду, создаёт задачу и проверяет что карточка видна."""
    page.goto(settings.AUTOTEST_BOARD_URL)
    expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=15000)

    page.get_by_role("button", name="Add task").first.click()
    expect(page.get_by_role("textbox", name="Task name...")).to_be_visible(timeout=5000)
    page.get_by_role("textbox", name="Task name...").fill(task_name)
    page.locator("#board-card-create").get_by_role("button", name="Add task").click()

    task_card = page.get_by_role("button").filter(
        has_text=re.compile(r"[A-Z]+-\d+")
    ).filter(has_text=task_name)
    expect(task_card).to_be_visible(timeout=10000)


def open_sidebar_menu(page: Page):
    """Кликает по кнопке '...' (три точки) в сайдбаре задачи/майлстоуна."""
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    more_btn = sidebar.locator('[class*="IconButton-module_Root"]:has(path[d^="M7.25 12"])').first
    more_btn.click()


@pytest.fixture()
def cleanup_task(request):
    """Регистрирует таймстемп теста для удаления всех созданных задач.

    Удаление происходит в attach_on_failure до page.close(),
    на той же странице — без отдельного браузера.

    Использование:
        cleanup_task["ts"] = _TS
    """
    task_info = {}
    request.node._cleanup_task_info = task_info
    yield task_info
