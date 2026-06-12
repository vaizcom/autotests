import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Auth, Header, Sidebar, SpaceSelector


@pytest.fixture()
def browser_context_args(browser_context_args):
    """Убираем storage_state — auth-тесты управляют сессией самостоятельно."""
    return {k: v for k, v in browser_context_args.items() if k != 'storage_state'}


def sign_in_and_go_to_space(page: Page):
    """Логинится и переходит в autotest space. Используется как setup в logout."""
    page.goto(f'{settings.BASE_URL}/auth/sign-in')
    page.get_by_test_id(Auth.EMAIL_INPUT).fill(settings.FRONTEND_EMAIL)
    page.get_by_test_id(Auth.EMAIL_SUBMIT).click()
    page.get_by_test_id(Auth.PASSWORD_INPUT).wait_for(state='visible', timeout=10000)
    page.get_by_test_id(Auth.PASSWORD_INPUT).fill(settings.FRONTEND_PASSWORD)
    page.get_by_test_id(Auth.PASSWORD_SUBMIT).click()
    expect(page.get_by_test_id(Sidebar.HOME)).to_be_visible(timeout=15000)

    page.get_by_test_id(Header.SPACE_SELECTOR).click()
    page.get_by_test_id(SpaceSelector.space(settings.AUTOTEST_SPACE_ID)).click()
    page.get_by_test_id(Sidebar.HOME).wait_for(state='visible', timeout=10000)


def home_screenshot_with_masks(page: Page) -> bytes:
    """Стабилизирует Home и возвращает скриншот с масками динамических элементов."""
    page.get_by_test_id(Sidebar.HOME).click()
    page.get_by_test_id(Sidebar.ARCHIVE).wait_for(state='visible', timeout=10000)
    page.mouse.move(640, 400)

    dynamic_masks = [
        page.locator('[class*="AsideNotificationsMenuItem-module_UnreadDot"]'),
        page.locator('[class*="NotificationsToggleButton-module_UnreadDot"]'),
        page.locator('[class*="MemberAvatar-module_Root"]'),
        page.locator('[class*="HomeScreen-module_Avatar"]'),
        page.locator('[class*="HomeScreen-module_Title"]'),
        page.locator('[class*="HomeScreen-module_TimeBlock"]'),
        page.get_by_test_id(Header.SPACE_SELECTOR),
        page.locator('[class*="HomeScreenCard-module_Root"]'),
        page.locator('[class*="HomeScreenTipCard-module_Tips"]'),
        page.locator('[class*="HomeScreenStuff-module_Root"]'),
        page.locator('[class*="TourBanner-module_Root"]'),
        page.locator('[class*="AffiliateBanner-module_Root"]'),
        page.locator('[class*="AsideMenu-module_Footer"]'),
    ]

    page.add_style_tag(
        content="""
        span[class*="AppVersion"] {
            background-color: #FF00FF !important;
            color: transparent !important;
            display: inline-block !important;
            min-height: 14px !important;
        }
    """
    )

    return page.screenshot(mask=dynamic_masks)
