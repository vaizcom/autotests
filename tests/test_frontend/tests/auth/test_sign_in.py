import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Auth, Header, Sidebar, SpaceSelector

pytestmark = [pytest.mark.frontend]


@pytest.fixture()
def browser_context_args(browser_context_args):
    """Убираем storage_state — тест проверяет логин самостоятельно."""
    return {k: v for k, v in browser_context_args.items() if k != 'storage_state'}


@allure.parent_suite('Frontend')
@allure.suite('Auth')
@allure.title('Sign in with email')
def test_sign_in_with_email(page: Page, assert_snapshot):
    with allure.step('Открытие страницы входа'):
        page.goto(f'{settings.BASE_URL}/auth/sign-in')

    with allure.step('Ввод email'):
        page.get_by_test_id(Auth.EMAIL_INPUT).fill(settings.FRONTEND_EMAIL)
        page.get_by_test_id(Auth.EMAIL_SUBMIT).click()

    with allure.step('Ввод пароля'):
        page.get_by_test_id(Auth.PASSWORD_INPUT).wait_for(state='visible', timeout=10000)
        page.get_by_test_id(Auth.PASSWORD_INPUT).fill(settings.FRONTEND_PASSWORD)
        page.get_by_test_id(Auth.PASSWORD_SUBMIT).click()

    with allure.step('Проверка успешного входа'):
        expect(page).not_to_have_url(f'{settings.BASE_URL}/auth/sign-in', timeout=15000)
        expect(page.get_by_test_id(Sidebar.HOME)).to_be_visible(timeout=15000)

    with allure.step('Переход в autotest space'):
        page.get_by_test_id(Header.SPACE_SELECTOR).click()
        page.get_by_test_id(SpaceSelector.space(settings.AUTOTEST_SPACE_ID)).click()
        page.get_by_test_id(Sidebar.HOME).wait_for(state='visible', timeout=10000)

    with allure.step('Сравнение скриншота'):
        page.get_by_test_id(Sidebar.ARCHIVE).wait_for(state='visible')

        # Фиксируем известный раздел → Home всегда активен в сайдбаре
        page.get_by_test_id(Sidebar.HOME).click()
        page.get_by_test_id(Sidebar.ARCHIVE).wait_for(state='visible')
        page.mouse.move(640, 400)  # убираем hover с Home

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

        page.mouse.move(640, 400)  # убираем hover после сворачивания
        page.wait_for_timeout(200)

        # Маски для динамических элементов которые меняются между запусками.
        # Если тест станет флакать — добавь сюда новые локаторы.
        dynamic_masks = [
            page.locator('[class*="AsideNotificationsMenuItem-module_UnreadDot"]'),  # точка уведомлений в сайдбаре
            page.locator('[class*="NotificationsToggleButton-module_UnreadDot"]'),  # точка уведомлений в хедере
            page.locator('[class*="MemberAvatar-module_Root"]'),  # аватар пользователя в хедере
            page.locator('[class*="HomeScreen-module_Avatar"]'),  # аватар/обложка на главной
            page.locator('[class*="HomeScreen-module_Title"]'),  # приветствие "Hello, auto!"
            page.locator('[class*="HomeScreen-module_TimeBlock"]'),  # время и дата
            page.get_by_test_id(Header.SPACE_SELECTOR),  # селектор Space в хедере
            page.locator('[class*="HomeScreenCard-module_Root"]'),  # карточки (задачи, документы, избранное)
            page.locator('[class*="HomeScreenTipCard-module_Tips"]'),  # совет недели
            page.locator('[class*="HomeScreenStuff-module_Root"]'),  # блок Spaces
            page.locator('[class*="TourBanner-module_Root"]'),  # баннер онбординга
            page.locator('[class*="AffiliateBanner-module_Root"]'),  # баннер "Invite people"
            page.locator('[class*="AsideMenu-module_Footer"]'),  # футер сайдбара
        ]

        # Версия приложения имеет высоту 0 — маска не работает, красим через CSS как Playwright mask
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

        screenshot = page.screenshot(mask=dynamic_masks)
        assert_snapshot(screenshot, name='sign_in_success.png', threshold=5.0)
