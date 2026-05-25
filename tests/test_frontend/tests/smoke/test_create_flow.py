import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Board, Header, Sidebar, SpaceSelector

pytestmark = [pytest.mark.frontend]

_SPACE_NAME = "Smoke Test Space"
_PROJECT_NAME = "Smoke Project"
_TASK_NAME = "New Task"


@pytest.mark.skipif(settings.FRONTEND_STAND == "prod", reason="Создание сущностей тестируется только на dev")
@allure.parent_suite("Frontend")
@allure.suite("Smoke")
@allure.title("Create space → project → task")
def test_create_space_with_project_and_task(page: Page, cleanup_space, assert_snapshot):
    """
    Smoke-тест: создание Space → wizard (Project + Board) → Task.
    Space удаляется через API в teardown.
    """
    # === SPACE ===
    with allure.step("Открытие приложения"):
        page.goto(f"{settings.BASE_URL}/")
        expect(page.get_by_test_id(Sidebar.HOME)).to_be_visible(timeout=15000)

    with allure.step(f"Создание Space: {_SPACE_NAME}"):
        page.get_by_test_id(Header.SPACE_SELECTOR).click()
        expect(page.get_by_test_id(SpaceSelector.CREATE)).to_be_visible(timeout=5000)
        page.get_by_test_id(SpaceSelector.CREATE).click()
        expect(page.get_by_role("button", name="Start creating")).to_be_visible(timeout=5000)
        page.get_by_role("button", name="Start creating").click()
        expect(page.get_by_role("textbox", name="Name")).to_be_visible(timeout=5000)
        page.get_by_role("textbox", name="Name").fill(_SPACE_NAME)
        page.get_by_role("button", name="Create space").click()

    with allure.step("Переключение в новый Space"):
        expect(page.get_by_role("button", name="Switch to Space")).to_be_visible(timeout=15000)
        page.get_by_role("button", name="Switch to Space").click()
        page.wait_for_url(lambda url: url != f"{settings.BASE_URL}/", timeout=10000)
        path = page.url.replace(settings.BASE_URL, "").strip("/")
        space_id = path.split("/")[0]
        cleanup_space.append(space_id)

    # === WIZARD: Set up your Workspace ===
    with allure.step(f"Wizard: настройка Workspace + Project '{_PROJECT_NAME}'"):
        expect(page.get_by_role("textbox", name="Space Name")).to_be_visible(timeout=10000)
        page.get_by_role("textbox", name="Space Name").clear()
        page.get_by_role("textbox", name="Space Name").fill(_SPACE_NAME)
        expect(page.get_by_role("textbox", name="My project")).to_be_visible(timeout=5000)
        page.get_by_role("textbox", name="My project").clear()
        page.get_by_role("textbox", name="My project").fill(_PROJECT_NAME)
        page.get_by_role("button", name="Continue").click()

    with allure.step("Пропуск приглашения (Invite a teammate)"):
        expect(page.get_by_role("button", name="Skip for now")).to_be_visible(timeout=10000)
        page.get_by_role("button", name="Skip for now").click()

    with allure.step("Ожидание загрузки Space"):
        expect(page.get_by_test_id(Sidebar.HOME)).to_be_visible(timeout=10000)

    # === PROJECT + TASK ===
    with allure.step(f"Открытие Project: {_PROJECT_NAME}"):
        project_link = page.locator("span").filter(has_text=_PROJECT_NAME).get_by_role("link")
        expect(project_link).to_be_visible(timeout=10000)
        project_link.click()
        expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=10000)

    with allure.step(f"Создание Task: {_TASK_NAME}"):
        page.get_by_test_id(Board.CREATE_TASK).first.click()
        expect(page.get_by_role("textbox", name="Task name...")).to_be_visible(timeout=5000)
        page.get_by_role("textbox", name="Task name...").fill(_TASK_NAME)
        page.locator("#board-card-create").get_by_role("button", name="Add task").click()

    with allure.step("Проверка Task на доске"):
        expect(page.get_by_text(_TASK_NAME)).to_be_visible(timeout=10000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(1000)

    with allure.step("Сравнение скриншота доски"):
        page.mouse.move(640, 400)
        page.wait_for_timeout(500)

        dynamic_masks = [
            page.locator('[class*="MemberAvatar-module_Root"]'),
            page.locator('[class*="HeaderSpaceSelector-module_Icon"]'),
            page.locator('[class*="AsideMenu-module_Footer"]'),
            page.locator('[class*="AsideNotificationsMenuItem-module_UnreadDot"]'),
            page.locator('[class*="NotificationsToggleButton-module_UnreadDot"]'),
            page.locator('[class*="TourBanner-module_Root"]'),
            page.locator('[class*="AffiliateBanner-module_Root"]'),
        ]

        page.add_style_tag(content='''
            span[class*="AppVersion"] {
                background-color: #FF00FF !important;
                color: transparent !important;
                display: inline-block !important;
                min-height: 14px !important;
            }
        ''')

        screenshot = page.screenshot(mask=dynamic_masks)
        assert_snapshot(screenshot, name="board_with_task.png", threshold=3.0)
