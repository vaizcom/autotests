import re
import sys

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, open_card

pytestmark = [pytest.mark.frontend]

_MULTISELECT_MOD = "Meta" if sys.platform == "darwin" else "Control"

# Display names тестовых юзеров — одинаковые на dev и prod
_FIRST = "FirstMember"
_SECOND = "SecondMember"

_ITEM_SELECTOR = '.szh-menu-container [class*="SelectFlySearch-module_ItemText"]'


def _open_assignee_dropdown(page, sidebar):
    """Открывает дропдаун Assign."""
    btn = sidebar.get_by_role("button", name=re.compile(r"^Assign"))
    expect(btn).to_be_visible(timeout=5000)
    btn.click()
    expect(page.locator(_ITEM_SELECTOR).first).to_be_visible(timeout=5000)


def _close_dropdown(page):
    """Закрывает дропдаун кликом по оверлею."""
    overlay = page.locator('[class*="FlyBlock-module_Overlay"]')
    if overlay.is_visible():
        overlay.click()
        expect(overlay).not_to_be_visible(timeout=5000)
    page.wait_for_timeout(300)


def _click_user(page, name: str, multiselect: bool = False):
    """Кликает по пользователю в дропдауне. С multiselect=True зажимает ⌘/Ctrl."""
    item = page.locator(_ITEM_SELECTOR).filter(has_text=name)
    expect(item).to_be_visible(timeout=5000)
    if multiselect:
        item.click(modifiers=[_MULTISELECT_MOD])
    else:
        item.click()


def _set_assignee(page, sidebar, name: str):
    """Устанавливает одного assignee (без ⌘/Ctrl+клик — заменяет текущих)."""
    _open_assignee_dropdown(page, sidebar)
    _click_user(page, name)
    _close_dropdown(page)
    expect(sidebar.get_by_role("button", name=re.compile(rf"Assign.*{name}"))).to_be_visible(timeout=5000)


def _add_assignee(page, sidebar, name: str):
    """Добавляет assignee через ⌘+клик (мультиселект)."""
    _open_assignee_dropdown(page, sidebar)
    _click_user(page, name, multiselect=True)
    _close_dropdown(page)


def _clear_assignees(page, sidebar):
    """Снимает всех assignee через ⌘+клик по каждому назначенному."""
    btn = sidebar.get_by_role("button", name=re.compile(r"^Assign"))
    btn_text = btn.inner_text()
    if "Not assigned" in btn_text:
        return
    _open_assignee_dropdown(page, sidebar)
    if _FIRST in btn_text:
        _click_user(page, _FIRST, multiselect=True)
    elif _SECOND in btn_text:
        _click_user(page, _SECOND, multiselect=True)
    else:
        # Мультиселект (кнопка = "Assign" без имён) — снять обоих
        _click_user(page, _FIRST, multiselect=True)
        _click_user(page, _SECOND, multiselect=True)
    _close_dropdown(page)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Assignee")
@allure.title("01. Назначить Assignee")
def test_01_assign_task_user(page: Page, soft_step, sidebar):
    """Назначает FirstMember исполнителем."""
    open_card(page, soft_step, TASK_NAME)

    def assign():
        sidebar.get_by_role("button", name="Assign Not assigned").click()
        expect(page.locator(_ITEM_SELECTOR).first).to_be_visible(timeout=5000)
        _click_user(page, _FIRST)
        _close_dropdown(page)
        expect(sidebar.get_by_role("button", name=re.compile(rf"Assign.*{_FIRST}"))).to_be_visible(timeout=5000)

    with allure.step(f"Назначить {_FIRST}"):
        soft_step("Исполнитель", assign)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Assignee")
@allure.title("02. Мультиселект (⌘ + клик)")
def test_02_multiselect_assignee(page: Page, soft_step, sidebar):
    """Добавляет SecondMember через ⌘+клик, оба назначены."""
    open_card(page, soft_step, TASK_NAME)

    with allure.step(f"Setup: назначить {_FIRST}"):
        _clear_assignees(page, sidebar)
        _set_assignee(page, sidebar, _FIRST)

    def multiselect():
        _add_assignee(page, sidebar, _SECOND)
        # При 2+ assignee кнопка показывает аватарки без имён — проверяем по кол-ву
        btn = sidebar.get_by_role("button", name=re.compile(r"^Assign"))
        avatars = btn.locator('[class*="MemberAvatar-module_Root"]')
        expect(avatars).to_have_count(2, timeout=5000)

    with allure.step(f"⌘ + {_SECOND} → оба назначены"):
        soft_step("Мультиселект", multiselect)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Assignee")
@allure.title("03. Убрать одного (⌘ + клик)")
def test_03_remove_one_assignee(page: Page, soft_step, sidebar):
    """Снимает FirstMember через ⌘+клик, остаётся SecondMember."""
    open_card(page, soft_step, TASK_NAME)

    with allure.step(f"Setup: {_FIRST} + {_SECOND}"):
        _clear_assignees(page, sidebar)
        _set_assignee(page, sidebar, _FIRST)
        _add_assignee(page, sidebar, _SECOND)

    def remove_one():
        _open_assignee_dropdown(page, sidebar)
        _click_user(page, _FIRST, multiselect=True)
        _close_dropdown(page)
        btn = sidebar.get_by_role("button", name=re.compile(r"^Assign"))
        expect(btn).to_contain_text(_SECOND, timeout=5000)
        expect(btn).not_to_contain_text(_FIRST, timeout=5000)

    with allure.step(f"⌘ + {_FIRST} → остался {_SECOND}"):
        soft_step("Убрать одного", remove_one)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Assignee")
@allure.title("04. Замена без ⌘")
def test_04_replace_assignee(page: Page, soft_step, sidebar):
    """Клик по FirstMember без ⌘ — заменяет SecondMember на FirstMember."""
    open_card(page, soft_step, TASK_NAME)

    with allure.step(f"Setup: назначить {_SECOND}"):
        _clear_assignees(page, sidebar)
        _set_assignee(page, sidebar, _SECOND)

    def replace():
        _open_assignee_dropdown(page, sidebar)
        _click_user(page, _FIRST)
        _close_dropdown(page)
        btn = sidebar.get_by_role("button", name=re.compile(r"^Assign"))
        expect(btn).to_contain_text(_FIRST, timeout=5000)
        expect(btn).not_to_contain_text(_SECOND, timeout=5000)

    with allure.step(f"Клик {_FIRST} без ⌘ → заменил {_SECOND}"):
        soft_step("Замена", replace)


@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.sub_suite("Assignee")
@allure.title("05. Снять Assignee")
def test_05_clear_assignee(page: Page, soft_step, sidebar):
    """Клик по назначенному пользователю без ⌘ снимает его."""
    open_card(page, soft_step, TASK_NAME)

    with allure.step(f"Setup: назначить {_FIRST}"):
        _clear_assignees(page, sidebar)
        _set_assignee(page, sidebar, _FIRST)

    def clear():
        _open_assignee_dropdown(page, sidebar)
        _click_user(page, _FIRST)
        _close_dropdown(page)
        expect(sidebar.get_by_role("button", name="Assign Not assigned")).to_be_visible(timeout=5000)

    with allure.step(f"Клик {_FIRST} → Not assigned"):
        soft_step("Снять", clear)
