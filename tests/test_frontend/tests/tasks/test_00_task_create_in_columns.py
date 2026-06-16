import re
from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Board, TaskCard

pytestmark = [pytest.mark.frontend]

_TS = datetime.now().strftime('%H%M%S')


@allure.parent_suite('Frontend')
@allure.suite('Tasks')
@allure.sub_suite('Create in Columns')
@allure.title('01. Создать задачу в каждой колонке борда')
def test_01_create_task_in_each_column(page: Page, soft_step):
    """Проверяет что задачу можно создать в каждой колонке борда."""
    page.goto(settings.AUTOTEST_BOARD_URL, timeout=60000)
    try:
        expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=15000)
    except Exception:
        page.reload()
        expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=15000)

    columns = page.get_by_test_id(Board.CREATE_TASK)
    column_count = columns.count()

    assert column_count > 0, 'На борде нет колонок с кнопкой создания задачи'

    for i in range(column_count):
        create_btn = columns.nth(i)
        task_name = f'columns_{i}_{_TS}'

        def create_in_column(btn=create_btn, name=task_name):
            btn.scroll_into_view_if_needed(timeout=5000)
            btn.click()

            form = page.locator('#board-card-create').last
            task_input = form.get_by_role('textbox', name='Task name...')
            expect(task_input).to_be_visible(timeout=5000)
            task_input.fill(name)
            form.get_by_role('button', name='Add task').click()

            task_card = page.get_by_role('button').filter(has_text=re.compile(r'[A-Z]+-\d+')).filter(has_text=name)
            expect(task_card).to_be_visible(timeout=10000)

            # Закрываем форму создания через Cancel
            cancel = form.get_by_text('Cancel')
            if cancel.is_visible():
                cancel.click()
            expect(page.locator('#board-card-create')).to_have_count(0, timeout=3000)

        with allure.step(f'Создание задачи в колонке {i + 1} из {column_count}'):
            soft_step(f'Колонка {i + 1}', create_in_column)


@allure.parent_suite('Frontend')
@allure.suite('Tasks')
@allure.sub_suite('Create in Columns')
@allure.title('99. Cleanup: удалить задачи из колонок')
def test_99_cleanup_column_tasks(page: Page):
    """Удаляет задачи col_*, созданные тестом создания в колонках."""
    page.goto(settings.AUTOTEST_BOARD_URL, timeout=60000)
    try:
        expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=15000)
    except Exception:
        page.reload()
        expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=15000)

    cards = page.get_by_role('button').filter(has_text=re.compile(r'[A-Z]+-\d+')).filter(has_text='col_')

    for _ in range(20):
        try:
            card = cards.filter(has_text=_TS).first
            expect(card).to_be_visible(timeout=3000)
        except Exception:
            break

        card.hover()
        card.get_by_test_id(TaskCard.MENU).click()

        delete_with_sub = page.get_by_text('Delete with subtasks')
        if delete_with_sub.is_visible(timeout=1000):
            delete_with_sub.click()
        else:
            page.get_by_text('Delete task').click()

        page.get_by_role('button', name='Proceed').click()
        page.wait_for_timeout(1000)
