import os
import re
from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Board

# ── Shared constants ──────────────────────────────────────────────────

_TS = os.environ.get("TEST_TS") or datetime.now().strftime("%H%M%S")
TASK_NAME = f"autotest_{_TS}"


# ── Session fixture: создание задачи + cleanup ────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _shared_task_lifecycle(playwright, auth_state, _configure_test_id):
    """Создаёт autotest задачу перед первым тестом, cleanup в finalizer."""
    browser = playwright.chromium.launch()
    ctx = browser.new_context(
        storage_state=auth_state,
        ignore_https_errors=True,
        viewport={"width": 1280, "height": 720},
    )
    page = ctx.new_page()
    create_task_on_board(page, TASK_NAME)
    page.close()
    ctx.close()
    browser.close()

    yield

    from tests.test_frontend.conftest import cleanup_board
    from tests.test_frontend.tests.milestones.conftest import cleanup_milestones

    browser = playwright.chromium.launch()
    ctx = browser.new_context(
        storage_state=auth_state,
        ignore_https_errors=True,
        viewport={"width": 1280, "height": 720},
    )
    page = ctx.new_page()
    cleanup_board(page)
    cleanup_milestones(page, keep_names=["Test milestone"])
    page.close()
    ctx.close()
    browser.close()


def find_subtask_row_by_name(container, name: str):
    """Строка в таблице подзадач с ID задачи (FRONT-XXX) и заданным именем."""
    return container.get_by_role("button").filter(
        has_text=re.compile(r"[A-Z]+-\d+")
    ).filter(has_text=name)


def _wait_board_ready(page: Page):
    """Ждёт полной загрузки борды: кнопка Add task + карточки или пустая колонка."""
    expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=25000)
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
        ).filter(has_text=card_name).first
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
        ).filter(has_text=card_name).first
        expect(task_card).to_be_visible(timeout=15000)
        task_card.click()
        sidebar = page.locator('[class*="RightSidebar-module_Root"]')
        expect(sidebar.get_by_role("heading", name=card_name)).to_be_visible(timeout=10000)

    with allure.step(f"Открытие карточки '{card_name}' в сайдбаре"):
        soft_step(f"Открытие '{card_name}' в сайдбаре", _open_sidebar)


def create_task_on_board(page: Page, task_name: str):
    """Открывает борду, создаёт задачу и проверяет что карточка видна."""
    page.goto(settings.AUTOTEST_BOARD_URL)
    expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=25000)

    page.get_by_test_id(Board.CREATE_TASK).first.click()
    expect(page.get_by_role("textbox", name="Task name...")).to_be_visible(timeout=5000)
    page.get_by_role("textbox", name="Task name...").fill(task_name)
    page.locator("#board-card-create").get_by_role("button", name="Add task").click()

    task_card = page.get_by_role("button").filter(
        has_text=re.compile(r"[A-Z]+-\d+")
    ).filter(has_text=task_name)
    expect(task_card).to_be_visible(timeout=10000)


def add_subtask(page: Page, subtask_name: str):
    """Добавляет подзадачу в открытом сайдбаре задачи."""
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    textbox = sidebar.get_by_role("textbox", name="Enter subtask name")
    expect(textbox).to_be_visible(timeout=5000)
    textbox.fill(subtask_name)
    page.keyboard.press("Enter")
    expect(find_subtask_row_by_name(sidebar, subtask_name)).to_be_visible(timeout=10000)


def create_subtasks(page: Page, card_name: str, subtask_names: list[str]):
    """Открывает карточку на борде и создаёт подзадачи."""
    card = page.get_by_role("button").filter(
        has_text=re.compile(r"[A-Z]+-\d+")
    ).filter(has_text=card_name)
    expect(card).to_be_visible(timeout=10000)
    card.click()
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    expect(sidebar.get_by_role("heading", name=card_name)).to_be_visible(timeout=10000)
    for name in subtask_names:
        add_subtask(page, name)


def _subtask_heading(container):
    """Возвращает первый heading секции подзадач."""
    return container.get_by_role("heading", name=re.compile(r"\d+ subtasks?")).first


def _scroll_to_subtasks(container):
    """Скроллит к секции подзадач."""
    heading = _subtask_heading(container)
    if heading.is_visible(timeout=5000):
        heading.evaluate("el => el.scrollIntoView({block: 'start'})")


def _is_subtask_section_collapsed(container):
    """Проверяет, свёрнута ли секция подзадач (инпут добавления не виден)."""
    return not container.get_by_role("textbox", name="Enter subtask name").first.is_visible(timeout=2000)


def _ensure_sidebar_open(page: Page, container, card_name: str):
    """Проверяет что сайдбар открыт с нужной карточкой, переоткрывает при необходимости."""
    task_heading = container.get_by_role("heading", name=card_name)
    if task_heading.is_visible(timeout=3000):
        return
    # Сайдбар закрыт — открываем карточку
    card = page.get_by_role("button").filter(
        has_text=re.compile(r"[A-Z]+-\d+")
    ).filter(has_text=card_name).first
    expect(card).to_be_visible(timeout=10000)
    for click_attempt in range(3):
        card.click()
        if task_heading.is_visible(timeout=5000):
            return
        page.wait_for_timeout(1000)


def wait_for_subtask_rows(page: Page, card_name: str, subtask_name: str, *, full_page: bool = False):
    """Ждёт загрузки строк подзадач с ретраями и reload."""
    container = page if full_page else page.locator('[class*="RightSidebar-module_Root"]')

    for attempt in range(4):
        # Убеждаемся что сайдбар открыт
        if not full_page:
            _ensure_sidebar_open(page, container, card_name)

        heading = _subtask_heading(container)

        # Скроллим к секции подзадач
        if heading.is_visible(timeout=5000):
            heading.evaluate("el => el.scrollIntoView({block: 'start'})")
        page.wait_for_timeout(1000)

        # Если секция свёрнута — раскрываем
        if heading.is_visible(timeout=3000) and _is_subtask_section_collapsed(container):
            heading.click()
            page.wait_for_timeout(1000)

        row = find_subtask_row_by_name(container, subtask_name)
        if row.is_visible(timeout=10000):
            return

        if attempt < 3:
            page.reload()
            if full_page:
                expect(page.get_by_role("heading", name=card_name).first).to_be_visible(timeout=15000)
            else:
                _wait_board_ready(page)
                _ensure_sidebar_open(page, container, card_name)
    expect(find_subtask_row_by_name(container, subtask_name)).to_be_visible(timeout=10000)


def toggle_subtask_complete(page: Page, subtask_name: str, *, full_page: bool = False):
    """Кликает чекбокс подзадачи по имени. Работает независимо от DOM-структуры."""
    container = page if full_page else page.locator('[class*="RightSidebar-module_Root"]')
    btn = container.get_by_role("button").filter(has_text=subtask_name)
    expect(btn).to_be_visible(timeout=15000)
    btn.evaluate("el => el.scrollIntoView({block: 'center'})")

    # JS-клик обходит перехват pointer events контейнером Subtasks-module_Root
    # Чекбокс внутри кнопки
    cb = btn.locator('label[role="checkbox"]')
    if cb.count() > 0:
        cb.evaluate("el => el.click()")
        return

    # Чекбокс в соседней ячейке — ищем ближайший контейнер с чекбоксами
    ancestor = btn.locator("xpath=ancestor::div[.//label[@role='checkbox']][1]")
    checkboxes = ancestor.locator('label[role="checkbox"]')

    if checkboxes.count() == 1:
        checkboxes.evaluate("el => el.click()")
        return

    # Несколько чекбоксов — совпадение по индексу с кнопками
    buttons = ancestor.get_by_role("button").filter(has_text=re.compile(r"[A-Z]+-\d+"))
    for i in range(buttons.count()):
        if subtask_name in buttons.nth(i).inner_text():
            checkboxes.nth(i).evaluate("el => el.click()")
            return

    raise AssertionError(f"Чекбокс для подзадачи '{subtask_name}' не найден")


def expect_subtask_counter(page: Page, card_name: str, text: str, *, full_page: bool = False):
    """Проверяет счётчик подзадач. При неудаче — reload + повторная проверка."""
    container = page if full_page else page.locator('[class*="RightSidebar-module_Root"]')
    try:
        expect(container.get_by_text(text)).to_be_visible(timeout=10000)
    except (AssertionError, Exception):
        page.reload()
        if full_page:
            expect(page.get_by_role("heading", name=card_name).first).to_be_visible(timeout=15000)
        else:
            _wait_board_ready(page)
            card = page.get_by_role("button").filter(
                has_text=re.compile(r"[A-Z]+-\d+")
            ).filter(has_text=card_name).first
            expect(card).to_be_visible(timeout=10000)
            card.click()
            expect(container.get_by_role("heading", name=card_name)).to_be_visible(timeout=10000)
        expect(container.get_by_text(text)).to_be_visible(timeout=10000)


def set_date(page: Page, date: str):
    """Устанавливает дату (due) в открытом сайдбаре задачи/майлстоуна."""
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    dates_btn = sidebar.get_by_role("button", name="Dates No dates set")
    expect(dates_btn).to_be_visible(timeout=5000)
    dates_btn.click()
    date_input = page.get_by_placeholder(re.compile(r"\d{2}\.\d{2}\.\d{4}")).first
    expect(date_input).to_be_visible(timeout=5000)
    date_input.click()
    date_input.press_sequentially(date, delay=50)
    page.keyboard.press("Tab")
    expect(date_input).to_have_value(date, timeout=5000)
    page.wait_for_timeout(1000)
    apply_btn = page.get_by_role("button", name="Apply")
    expect(apply_btn).to_be_enabled(timeout=10000)
    apply_btn.click()


def fill_description(page: Page, text: str):
    """Заполняет описание в tiptap-редакторе открытого сайдбара."""
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    # Описание — .tiptap вне секции комментариев (работает на задачах и майлстоунах)
    editor = sidebar.locator(
        '//*[contains(@class, "tiptap") and not(ancestor::*[contains(@class, "Comment")])]'
    ).first
    expect(editor).to_be_visible(timeout=10000)
    editor.scroll_into_view_if_needed()
    editor.click()
    expect(editor).to_have_attribute("contenteditable", "true", timeout=5000)
    editor.fill(text)
    expect(editor).to_contain_text(text, timeout=5000)


def add_comment(page: Page, comment_text: str):
    """Вводит и отправляет комментарий в открытом сайдбаре задачи/майлстоуна."""
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    toolbar = sidebar.locator('[class*="CommentToolbar-module"]').first
    expect(toolbar).to_be_visible(timeout=5000)
    toolbar.scroll_into_view_if_needed()
    comment_editor = toolbar.locator('xpath=ancestor::div[contains(@class, "Comment")]').locator(".tiptap")
    expect(comment_editor).to_be_visible(timeout=5000)
    comment_editor.click()
    comment_editor.fill(comment_text)
    send_btn = sidebar.locator('[class*="CommentToolbar-module_Right"]').get_by_role("button").last
    expect(send_btn).to_be_enabled(timeout=5000)
    send_btn.click()


def create_milestone_from_dropdown(page: Page, milestone_name: str):
    """Создаёт майлстоун из dropdown поля Milestones в открытом сайдбаре."""
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    milestones_btn = sidebar.get_by_role("button", name=re.compile(r"^Milestones"))
    expect(milestones_btn).to_be_visible(timeout=5000)
    milestones_btn.click()
    create_item = page.get_by_role("menuitem", name="Create milestone")
    expect(create_item).to_be_visible(timeout=5000)
    create_item.locator("div").first.click()
    name_input = page.get_by_role("textbox", name="Type name")
    expect(name_input).to_be_visible(timeout=5000)
    name_input.fill(milestone_name)
    page.get_by_role("button", name="Add", exact=True).click()
    expect(milestones_btn.filter(has_text=milestone_name)).to_be_visible(timeout=5000)


def remove_milestone_from_dropdown(page: Page, milestone_name: str):
    """Снимает майлстоун в dropdown поля Milestones в открытом сайдбаре."""
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    milestones_btn = sidebar.get_by_role("button", name=re.compile(r"^Milestones"))
    expect(milestones_btn).to_be_visible(timeout=5000)
    milestones_btn.click()
    item = page.get_by_role("menuitem", name=milestone_name)
    expect(item).to_be_visible(timeout=5000)
    item.click()


def open_sidebar_menu(page: Page):
    """Кликает по кнопке '...' (три точки) в сайдбаре задачи/майлстоуна."""
    sidebar = page.locator('[class*="RightSidebar-module_Root"]')
    more_btn = sidebar.locator('[class*="IconButton-module_Root"]:has(path[d^="M7.25 12"])').first
    expect(more_btn).to_be_visible(timeout=5000)
    more_btn.click()


def open_as_page(page: Page, card_name: str):
    """Открывает задачу/майлстоун на полную страницу через меню '...' → 'Open as page'."""
    open_sidebar_menu(page)
    page.get_by_text("Open as page").click()
    expect(page.locator('[class*="RightSidebar-module_Root"]')).not_to_be_visible(timeout=5000)
    expect(page.get_by_role("heading", name=card_name).first).to_be_visible(timeout=15000)


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
