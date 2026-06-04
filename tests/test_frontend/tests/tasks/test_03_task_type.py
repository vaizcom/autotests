import re
import sys

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, open_card

pytestmark = [pytest.mark.frontend]

_MULTISELECT_MOD = "Meta" if sys.platform == "darwin" else "Control"


def _open_type_dropdown(page, sidebar):
    """Открывает дропдаун Types."""
    btn = sidebar.get_by_role("button", name=re.compile(r"^Types"))
    expect(btn).to_be_visible(timeout=5000)
    btn.click()
    expect(page.get_by_role("menuitem").first).to_be_visible(timeout=5000)


def _close_dropdown(page):
    """Закрывает дропдаун нажатием Escape."""
    menuitem = page.get_by_role("menuitem").first
    if not menuitem.is_visible(timeout=1000):
        return
    page.keyboard.press("Escape")
    expect(menuitem).not_to_be_visible(timeout=5000)


def _set_type(page, sidebar, type_name: str):
    """Устанавливает один тип (без модификатора — заменяет текущий)."""
    _open_type_dropdown(page, sidebar)
    page.get_by_role("menuitem", name=type_name).click()
    _close_dropdown(page)
    expect(sidebar.get_by_role("button", name=re.compile(rf"Types.*{type_name}"))).to_be_visible(timeout=5000)


def _add_type(page, sidebar, type_name: str):
    """Добавляет тип через ⌘+клик (мультиселект)."""
    _open_type_dropdown(page, sidebar)
    page.get_by_role("menuitem", name=type_name).click(modifiers=[_MULTISELECT_MOD])
    _close_dropdown(page)


def _clear_type(page, sidebar):
    """Сбрасывает все типы через Clear type."""
    _open_type_dropdown(page, sidebar)
    clear = page.get_by_text("Clear type")
    if clear.is_visible(timeout=2000):
        clear.click()
        page.wait_for_timeout(500)
    _close_dropdown(page)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Type")
@allure.title("01. Установить Type Green")
def test_01_set_task_type(page: Page, soft_step, sidebar):
    """Открывает дропдаун, проверяет отображение элементов, выбирает Green."""
    open_card(page, soft_step, TASK_NAME)

    def set_type():
        _open_type_dropdown(page, sidebar)

        # Проверка отображения элементов дропдауна
        expect(page.get_by_role("textbox", name="Type to search...")).to_be_visible(timeout=5000)
        expect(page.get_by_text("New type")).to_be_visible(timeout=5000)

        page.get_by_role("menuitem", name="Green").click()
        expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Green"))).to_be_visible(timeout=5000)

    with allure.step("Выбор типа Green"):
        soft_step("Тип", set_type)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Type")
@allure.title("02. Search в дропдауне")
def test_02_search_task_type(page: Page, soft_step, sidebar):
    """Проверяет фильтрацию по поиску в дропдауне Types."""
    open_card(page, soft_step, TASK_NAME)

    def search_type():
        _open_type_dropdown(page, sidebar)
        search = page.get_by_role("textbox", name="Type to search...")
        search.fill("Green")
        expect(page.get_by_role("menuitem", name="Green")).to_be_visible(timeout=5000)
        expect(page.get_by_role("menuitem", name="Blue")).not_to_be_visible(timeout=3000)
        expect(page.get_by_role("menuitem", name="Pink")).not_to_be_visible(timeout=3000)
        _close_dropdown(page)

    with allure.step("Поиск Green в дропдауне"):
        soft_step("Search", search_type)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Type")
@allure.title("03. Мультиселект Types (⌘ + клик)")
def test_03_multiselect_task_type(page: Page, soft_step, sidebar):
    """Устанавливает Green, добавляет Blue через ⌘+клик, проверяет что оба видны."""
    open_card(page, soft_step, TASK_NAME)

    # Гарантируем начальное состояние: Green (clear → set)
    with allure.step("Setup: установить Green"):
        _clear_type(page, sidebar)
        _set_type(page, sidebar, "Green")

    def multiselect():
        _add_type(page, sidebar, "Blue")
        expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Green"))).to_be_visible(timeout=5000)
        expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Blue"))).to_be_visible(timeout=5000)

    with allure.step("⌘ + Blue → Green + Blue"):
        soft_step("Мультиселект", multiselect)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Type")
@allure.title("04. Убрать один Type (⌘ + клик)")
def test_04_remove_one_task_type(page: Page, soft_step, sidebar):
    """Устанавливает Green+Blue, снимает Green через ⌘+клик, остаётся Blue."""
    open_card(page, soft_step, TASK_NAME)

    # Гарантируем начальное состояние: Green + Blue (clear → set → add)
    with allure.step("Setup: Green + Blue"):
        _clear_type(page, sidebar)
        _set_type(page, sidebar, "Green")
        _add_type(page, sidebar, "Blue")

    def remove_one():
        _open_type_dropdown(page, sidebar)
        page.get_by_role("menuitem", name="Green").click(modifiers=[_MULTISELECT_MOD])
        _close_dropdown(page)
        expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Blue"))).to_be_visible(timeout=5000)
        expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Green"))).not_to_be_visible(timeout=3000)

    with allure.step("⌘ + Green → остался Blue"):
        soft_step("Убрать один", remove_one)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Type")
@allure.title("05. Замена Types без ⌘")
def test_05_replace_task_type(page: Page, soft_step, sidebar):
    """Устанавливает Green+Blue, клик по Pink без ⌘ — заменяет все на Pink."""
    open_card(page, soft_step, TASK_NAME)

    # Гарантируем начальное состояние: Green + Blue
    with allure.step("Setup: Green + Blue"):
        _clear_type(page, sidebar)
        _set_type(page, sidebar, "Green")
        _add_type(page, sidebar, "Blue")

    def replace_with_pink():
        _open_type_dropdown(page, sidebar)
        page.get_by_role("menuitem", name="Pink").click()
        expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Pink"))).to_be_visible(timeout=5000)
        expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Green"))).not_to_be_visible(timeout=3000)
        expect(sidebar.get_by_role("button", name=re.compile(r"Types.*Blue"))).not_to_be_visible(timeout=3000)

    with allure.step("Клик Pink без ⌘ → только Pink"):
        soft_step("Замена на Pink", replace_with_pink)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Type")
@allure.title("06. Clear type")
def test_06_clear_task_type(page: Page, soft_step, sidebar):
    """Устанавливает тип, сбрасывает через Clear type."""
    open_card(page, soft_step, TASK_NAME)

    # Гарантируем что тип установлен
    with allure.step("Setup: установить Green"):
        _clear_type(page, sidebar)
        _set_type(page, sidebar, "Green")

    def clear_type():
        _open_type_dropdown(page, sidebar)
        page.get_by_text("Clear type").click()
        expect(sidebar.get_by_role("button", name="Types Select type")).to_be_visible(timeout=5000)

    with allure.step("Clear type → пустое состояние"):
        soft_step("Clear type", clear_type)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Type")
@allure.title("07. New type: форма создания типа")
def test_07_create_new_task_type(page: Page, soft_step, sidebar):
    """Проверяет форму создания нового типа: инпут, кнопка Add, цвета и иконки."""
    open_card(page, soft_step, TASK_NAME)

    def check_new_type_form():
        _open_type_dropdown(page, sidebar)
        page.get_by_text("New type").click()

        form = page.locator('[class*="CreateNewBoardType-module_Root"]')
        expect(form).to_be_visible(timeout=5000)

        # Кнопка Add видна и доступна при вводе имени
        name_input = form.get_by_role("textbox", name="Type name")
        add_btn = form.get_by_role("button", name="Add", exact=True)
        expect(add_btn).to_be_visible(timeout=5000)
        name_input.fill("Test")
        expect(add_btn).to_be_enabled(timeout=5000)
        name_input.clear()

        # Вкладка Colors видна, можно кликнуть цвет
        colors_tab = form.get_by_role("button", name="Colors")
        expect(colors_tab).to_be_visible(timeout=5000)
        color_items = form.locator('[class*="StylerIcon-module_Root"]')
        expect(color_items.first).to_be_visible(timeout=5000)
        color_items.nth(2).click()

        # Переключение на Icons
        icons_tab = form.get_by_role("button", name="Icons")
        expect(icons_tab).to_be_visible(timeout=5000)
        icons_tab.click()
        icon_items = form.locator('[class*="StylerIcon-module_Root"]')
        expect(icon_items.first).to_be_visible(timeout=5000)
        icon_items.first.click()

        # Возвращаемся на Colors
        colors_tab.click()
        expect(color_items.first).to_be_visible(timeout=5000)

        _close_dropdown(page)

    with allure.step("Форма New type: инпут, Add, Colors, Icons"):
        soft_step("Форма New type", check_new_type_form)
