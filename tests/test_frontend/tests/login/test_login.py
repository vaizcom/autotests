import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings

pytestmark = [pytest.mark.frontend]


@pytest.fixture()
def browser_context_args(browser_context_args):
    """Убираем storage_state — тест проверяет сам логин."""
    return {k: v for k, v in browser_context_args.items() if k != "storage_state"}


@allure.parent_suite("Frontend")
@allure.suite("Auth")
@allure.title("Sign in with email")
def test_sign_in_with_email(page: Page, assert_snapshot):
    with allure.step("Открытие страницы входа"):
        page.goto(f"{settings.BASE_URL}/auth/sign-in")
    with allure.step("Ввод учётных данных"):
        page.get_by_role("textbox", name="Email").fill(settings.FRONTEND_EMAIL)
        page.get_by_role("textbox", name="Password").fill(settings.FRONTEND_PASSWORD)

    with allure.step("Нажатие кнопки Continue with Email"):
        page.get_by_role("button", name="Continue with Email").click()

    with allure.step("Проверка успешного входа"):
        expect(page).not_to_have_url(f"{settings.BASE_URL}/auth/sign-in", timeout=15000)
        expect(page.get_by_role("link", name="Home")).to_be_visible(timeout=15000)

    with allure.step("Сравнение скриншота"):
        page.get_by_role("link", name="Archive").wait_for(state="visible")

        # Фиксируем известный раздел → Home всегда активен в сайдбаре
        page.get_by_role("link", name="Home").click()
        page.get_by_role("link", name="Archive").wait_for(state="visible")
        page.mouse.move(640, 400)  # убираем hover с Home

        # Сворачиваем все раскрытые секции сайдбара → фиксируем известное состояние
        for arrow in page.locator('[class*="_ArrowBox_"]').all():
            is_expanded = arrow.evaluate("""el => {
                const header = el.parentElement;
                let next = header?.nextElementSibling;
                while (next) {
                    if (next.className?.includes('CollabsedBox')) {
                        return next.offsetHeight > 0;
                    }
                    next = next.nextElementSibling;
                }
                return false;
            }""")
            if is_expanded:
                arrow.click()
                # Ждём пока конкретная секция полностью свернётся (высота = 0)
                arrow.evaluate("""el => new Promise(resolve => {
                    const check = () => {
                        const header = el.parentElement;
                        let next = header?.nextElementSibling;
                        while (next) {
                            if (next.className?.includes('CollabsedBox')) {
                                if (next.offsetHeight === 0) { resolve(); return; }
                                break;
                            }
                            next = next.nextElementSibling;
                        }
                        setTimeout(check, 50);
                    };
                    check();
                })""")

        page.mouse.move(640, 400)  # убираем hover после сворачивания
        page.wait_for_timeout(200)

        # Маски для динамических элементов которые меняются между запусками.
        # Если тест станет флакать — добавь сюда новые локаторы.
        dynamic_masks = [
            page.locator('[class*="AsideNotificationsMenuItem-module_UnreadDot"]'),  # точка уведомлений в сайдбаре
            page.locator('[class*="NotificationsToggleButton-module_UnreadDot"]'),   # точка уведомлений в хедере
            page.locator('[class*="MemberAvatar-module_Root"]'),          # аватар пользователя в хедере
            page.locator('[class*="HomeScreen-module_Avatar"]'),          # аватар/обложка на главной
            page.locator('[class*="HomeScreen-module_Title"]'),           # приветствие "Hello, auto!"
            page.locator('[class*="HomeScreen-module_TimeBlock"]'),       # время и дата
            page.locator('[class*="HeaderSpaceSelector-module_Inner"]'),  # селектор Space в хедере
            page.locator('[class*="HomeScreenCard-module_Root"]'),        # карточки (задачи, документы, избранное)
            page.locator('[class*="HomeScreenTipCard-module_Tips"]'),     # совет недели
            page.locator('[class*="HomeScreenStuff-module_Root"]'),       # блок Spaces
            page.locator('[class*="TourBanner-module_Root"]'),            # баннер онбординга
            page.locator('[class*="AffiliateBanner-module_Root"]'),       # баннер "Invite people"
            page.locator('[class*="AsideMenu-module_Footer"]'),           # футер сайдбара
        ]

        # Версия приложения имеет высоту 0 — маска не работает, красим через CSS как Playwright mask
        page.add_style_tag(content='''
            span[class*="AppVersion"] {
                background-color: #FF00FF !important;
                color: transparent !important;
                display: inline-block !important;
                min-height: 14px !important;
            }
        ''')

        screenshot = page.screenshot(mask=dynamic_masks)
        assert_snapshot(screenshot, name="sign_in_success.png", threshold=5.0)
