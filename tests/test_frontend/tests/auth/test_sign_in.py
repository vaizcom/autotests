import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Auth, Sidebar
from tests.test_frontend.tests.auth.conftest import sign_in_and_go_to_space, home_screenshot_with_masks

pytestmark = [pytest.mark.frontend]


@allure.parent_suite('Frontend')
@allure.suite('Auth')
@allure.title('Sign in with email')
def test_sign_in_with_email(page: Page, assert_snapshot):
    with allure.step('Вход и переход в autotest space'):
        sign_in_and_go_to_space(page)

    with allure.step('Сравнение скриншота'):
        # Сворачиваем раскрытые секции сайдбара → фиксируем известное состояние
        # ADD_DOC один test-id на обе секции (Space Docs / Personal Docs) → .first/.last
        collapsible = [
            (Sidebar.PROJECTS, page.get_by_test_id(Sidebar.ADD_PROJECT)),
            (Sidebar.SPACE_DOCS, page.get_by_test_id(Sidebar.ADD_DOC).first),
            (Sidebar.PERSONAL_DOCS, page.get_by_test_id(Sidebar.ADD_DOC).last),
        ]
        for section_id, child in collapsible:
            if child.is_visible(timeout=1000):
                page.get_by_test_id(section_id).click()
                page.wait_for_timeout(500)

        page.mouse.move(640, 400)
        page.wait_for_timeout(200)

        screenshot = home_screenshot_with_masks(page)
        assert_snapshot(screenshot, name='sign_in_success.png', threshold=5.0)
