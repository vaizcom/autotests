import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, open_card

pytestmark = [pytest.mark.frontend]


@allure.parent_suite('Frontend')
@allure.suite('Tasks')
@allure.sub_suite('Complete')
@allure.title('01. Завершить Task')
def test_01_complete_task(page: Page, soft_step, sidebar):
    """Отмечает задачу как выполненную и снимает отметку.
    Проверяет чекбокс и в сайдбаре, и на карточке борда."""
    open_card(page, soft_step, TASK_NAME)

    sidebar_checkbox = sidebar.locator('label[role="checkbox"]').first
    board_card = page.get_by_role('button').filter(has_text=re.compile(r'[A-Z]+-\d+')).filter(has_text=TASK_NAME).first
    board_toggle = board_card.locator('input[data-test-id*="complete-toggle"]')

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
