import re

import allure
import pytest
from playwright.sync_api import Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, _TS, open_card

pytestmark = [pytest.mark.frontend]

_CUSTOM_TEXT_VALUE = f'Test value {_TS}'


@allure.parent_suite('Frontend')
@allure.suite('Tasks')
@allure.sub_suite('Custom Fields')
@allure.title('01. Заполнить Custom Field')
def test_01_fill_task_custom_field(page: Page, soft_step, sidebar):
    """Заполняет кастомное текстовое поле задачи."""
    open_card(page, soft_step, TASK_NAME)

    def fill_custom_text():
        sidebar.get_by_role('button', name=re.compile(r'^Text')).first.click()
        text_input = page.get_by_placeholder('Empty').first
        text_input.clear()
        text_input.fill(_CUSTOM_TEXT_VALUE)
        page.keyboard.press('Escape')

    with allure.step(f'Заполнение кастомного поля: {_CUSTOM_TEXT_VALUE}'):
        soft_step('Кастомное поле Text', fill_custom_text)
