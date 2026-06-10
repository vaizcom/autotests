import allure
import pytest
from playwright.sync_api import Page

pytestmark = [pytest.mark.frontend]


@allure.parent_suite('Frontend')
@allure.suite('Tasks')
@allure.sub_suite('Lifecycle')
@allure.title('99. Очистка')
def test_99_cleanup_task_board(page: Page):
    """Удаляет все карточки с борды и архивирует созданные майлстоуны."""
    from tests.test_frontend.conftest import cleanup_board
    from tests.test_frontend.tests.milestones.conftest import cleanup_milestones

    cleanup_board(page)
    cleanup_milestones(page, keep_names=['Test milestone'])
