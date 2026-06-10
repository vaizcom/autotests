import allure
import pytest
from playwright.sync_api import Page

from tests.test_frontend.tests.tasks.conftest import TASK_NAME, _TS, open_card, add_comment

pytestmark = [pytest.mark.frontend]

_COMMENT = f'Test comment {_TS}'


@allure.parent_suite('Frontend')
@allure.suite('Tasks')
@allure.sub_suite('Comments')
@allure.title('01. Добавить Comment')
def test_01_add_task_comment(page: Page, soft_step):
    """Добавляет комментарий к задаче."""
    open_card(page, soft_step, TASK_NAME)

    with allure.step(f'Комментарий: {_COMMENT}'):
        soft_step('Комментарий', lambda: add_comment(page, _COMMENT))
