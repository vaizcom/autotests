import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core.locators import TaskCard
from tests.test_frontend.tests.tasks.conftest import (
    TASK_NAME, get_board_card, open_card, open_sidebar_menu, wait_for_card,
)

pytestmark = [pytest.mark.frontend]


@allure.parent_suite('Frontend')
@allure.suite('Tasks')
@allure.sub_suite('Complete')
@allure.title('01. Завершить Task')
def test_01_complete_task(page: Page, soft_step, sidebar):
    """Отмечает задачу как выполненную (Complete) и снимает отметку(UnComplete).
    Проверяет чекбокс и в сайдбаре, и на карточке борды."""
    open_card(page, soft_step, TASK_NAME)

    sidebar_checkbox = sidebar.locator('label[role="checkbox"]').first
    board_card = get_board_card(page, TASK_NAME)
    board_toggle = board_card.locator('input[data-test-id*="complete-toggle"]')

    # Нормализуем состояние — задача должна быть незавершённой
    if sidebar_checkbox.locator('input').is_checked():
        sidebar_checkbox.click()
        expect(sidebar_checkbox.locator('input')).not_to_be_checked(timeout=5000)

    def complete_task():
        sidebar_checkbox.click()
        expect(sidebar_checkbox.locator('input')).to_be_checked(timeout=5000)

    def check_board_complete():
        expect(board_toggle).to_be_checked(timeout=10000)

    def uncomplete_task():
        sidebar_checkbox.click()
        expect(sidebar_checkbox.locator('input')).not_to_be_checked(timeout=5000)

    def check_board_uncomplete():
        expect(board_toggle).not_to_be_checked(timeout=10000)

    with allure.step('Complete'):
        soft_step('Complete в сайдбаре', complete_task)
        soft_step('Complete на карточке борда', check_board_complete)

    with allure.step('Uncomplete'):
        soft_step('Uncomplete в сайдбаре', uncomplete_task)
        soft_step('Uncomplete на карточке борда', check_board_uncomplete)


@allure.parent_suite('Frontend')
@allure.suite('Tasks')
@allure.sub_suite('Complete')
@allure.title('02. Complete кликом на карточке борда')
def test_02_complete_from_board(page: Page, soft_step, sidebar):
    """Завершает задачу кликом по чекбоксу на карточке борда (без открытия сайдбара)."""
    wait_for_card(page, TASK_NAME)

    board_card = get_board_card(page, TASK_NAME)
    board_label = board_card.locator('label[role="checkbox"]')
    board_input = board_card.locator('input[data-test-id*="complete-toggle"]')

    # Нормализуем состояние — задача должна быть незавершённой
    if board_input.is_checked():
        board_label.click()
        expect(board_input).not_to_be_checked(timeout=5000)

    def complete_from_board():
        board_label.click()
        expect(board_input).to_be_checked(timeout=5000)

    def uncomplete_from_board():
        board_label.click()
        expect(board_input).not_to_be_checked(timeout=5000)

    def open_and_check_sidebar(expected_checked):
        board_card.click()
        sidebar_checkbox = sidebar.locator('label[role="checkbox"]').first
        if expected_checked:
            expect(sidebar_checkbox.locator('input')).to_be_checked(timeout=5000)
        else:
            expect(sidebar_checkbox.locator('input')).not_to_be_checked(timeout=5000)
        page.keyboard.press('Escape')

    with allure.step('Complete на борде'):
        soft_step('Complete', complete_from_board)
        soft_step('Complete в сайдбаре', lambda: open_and_check_sidebar(True))

    with allure.step('Uncomplete на борде'):
        soft_step('Uncomplete', uncomplete_from_board)
        soft_step('Uncomplete в сайдбаре', lambda: open_and_check_sidebar(False))


@allure.parent_suite('Frontend')
@allure.suite('Tasks')
@allure.sub_suite('Complete')
@allure.title('03. Complete через меню карточки на борде')
def test_03_complete_from_card_menu(page: Page, soft_step, sidebar):
    """Завершает задачу через контекстное меню карточки на борде."""
    wait_for_card(page, TASK_NAME)

    board_card = get_board_card(page, TASK_NAME)
    board_input = board_card.locator('input[data-test-id*="complete-toggle"]')

    # Нормализуем состояние — задача должна быть незавершённой
    if board_input.is_checked():
        board_card.locator('label[role="checkbox"]').click()
        expect(board_input).not_to_be_checked(timeout=5000)

    def click_card_menu_completed():
        board_card.hover()
        board_card.get_by_test_id(TaskCard.MENU).click()
        menu = page.locator('[class*="szh-menu"]').filter(has_text='Completed')
        expect(menu.first).to_be_visible(timeout=5000)
        menu.first.get_by_text('Completed').click()

    def complete_via_menu():
        click_card_menu_completed()
        expect(board_input).to_be_checked(timeout=5000)

    def uncomplete_via_menu():
        click_card_menu_completed()
        expect(board_input).not_to_be_checked(timeout=5000)

    with allure.step('Complete через меню карточки'):
        soft_step('Complete', complete_via_menu)

    with allure.step('Uncomplete через меню карточки'):
        soft_step('Uncomplete', uncomplete_via_menu)


@allure.parent_suite('Frontend')
@allure.suite('Tasks')
@allure.sub_suite('Complete')
@allure.title('04. Complete через меню сайдбара')
def test_04_complete_from_sidebar_menu(page: Page, soft_step, sidebar):
    """Завершает задачу через меню '...' в сайдбаре."""
    open_card(page, soft_step, TASK_NAME)

    sidebar_checkbox = sidebar.locator('label[role="checkbox"]').first
    cb_input = sidebar_checkbox.locator('input')

    # Нормализуем состояние — задача должна быть незавершённой
    if cb_input.is_checked():
        sidebar_checkbox.click()
        expect(cb_input).not_to_be_checked(timeout=5000)

    def click_sidebar_menu_completed():
        open_sidebar_menu(page)
        menu = page.locator('[class*="szh-menu"]').filter(has_text='Completed')
        expect(menu.first).to_be_visible(timeout=5000)
        menu.first.get_by_text('Completed').click()

    def complete_via_sidebar_menu():
        click_sidebar_menu_completed()
        cb = sidebar.locator('label[role="checkbox"]').first
        expect(cb.locator('input')).to_be_checked(timeout=10000)

    def uncomplete_via_sidebar_menu():
        click_sidebar_menu_completed()
        cb = sidebar.locator('label[role="checkbox"]').first
        expect(cb.locator('input')).not_to_be_checked(timeout=10000)

    with allure.step('Complete через меню сайдбара'):
        soft_step('Complete', complete_via_sidebar_menu)

    with allure.step('Uncomplete через меню сайдбара'):
        soft_step('Uncomplete', uncomplete_via_sidebar_menu)
