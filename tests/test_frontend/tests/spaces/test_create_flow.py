import re

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings

pytestmark = [pytest.mark.frontend]

_SPACE_NAME = "Smoke Test Space"
_PROJECT_NAME = "New Project"
_PROJECT_SLUG = "SMOKETEST"
_BOARD_NAME = "Default board"
_TASK_NAME = "New Task"


@pytest.mark.skipif(settings.FRONTEND_STAND == "prod", reason="Создание сущностей тестируется только на dev")
@allure.parent_suite("Frontend")
@allure.suite("Smoke")
@allure.title("Create space → project → board → task")
def test_create_space_with_project_board_task(page: Page, cleanup_space, assert_snapshot):
    """
    Smoke-тест, проверяющий полный флоу создания сущностей: Space → Project → Board → Task.
    По завершении скриншот доски сравнивается с baseline. Space удаляется через API в teardown.
    Тест не запускается на проде, так как создание сущностей тестируется только на dev.
    """
    # === SPACE ===
    with allure.step("Открытие приложения"):
        page.goto(f"{settings.BASE_URL}/")
        expect(page.get_by_role("link", name="Home")).to_be_visible(timeout=15000)

    with allure.step(f"Создание Space: {_SPACE_NAME}"):
        page.get_by_text("Marina's Space").first.click()
        page.get_by_text("Create new space").click()
        page.get_by_role("button", name="Start creating").click()
        page.get_by_role("textbox", name="Name").fill(_SPACE_NAME)
        page.get_by_role("button", name="Create space").click()

    with allure.step("Переключение в новый Space"):
        expect(page.get_by_role("button", name="Switch to Space")).to_be_visible(timeout=15000)
        page.get_by_role("button", name="Switch to Space").click()
        page.wait_for_url(lambda url: url != f"{settings.BASE_URL}/", timeout=10000)
        space_id = page.url.rstrip("/").split("/")[-1]
        cleanup_space.append(space_id)
        expect(page.get_by_role("link", name="Home")).to_be_visible(timeout=10000)

    # === PROJECT ===
    with allure.step(f"Создание Project: {_PROJECT_NAME}"):
        page.get_by_text("Add project").click()
        page.get_by_role("button", name="Start creating").click()
        page.get_by_role("textbox", name="Name & Appearance").fill(_PROJECT_NAME)
        page.get_by_role("textbox", name="Slug ?").fill(_PROJECT_SLUG)

    with allure.step("Выбор цвета и иконки проекта"):
        # Открываем пикер внешнего вида
        page.locator("#create-new-project-modal-enter-data").get_by_role("button").click()
        page.get_by_title("green").locator("span").nth(1).click()
        page.get_by_role("button", name="Icons").click()
        page.get_by_title("Checkbox").get_by_role("img").click()
        page.keyboard.press("Escape")

    with allure.step("Подтверждение создания Project"):
        page.get_by_role("button", name="Create project").click()

    with allure.step("Открытие Project"):
        page.get_by_role("button", name="Continue").click()
        expect(page.get_by_role("button", name="Open project")).to_be_visible(timeout=10000)
        page.get_by_role("button", name="Open project").click()

    with allure.step("Проверка Project"):
        # Ждём загрузку страницы проекта — "Add board" появляется в пустом проекте
        expect(page.get_by_text("Add board")).to_be_visible(timeout=10000)

    # === BOARD ===
    with allure.step(f"Создание Board: {_BOARD_NAME}"):
        page.get_by_text("Add board").click()
        page.get_by_role("button", name="Start creating").click()
        page.get_by_text("DefaultA simple board with a").click()
        page.get_by_role("button", name="Continue").click()
        page.get_by_role("textbox", name="Board name").fill(_BOARD_NAME)
        # Подтверждение имени борды — кнопка внутри поля ввода
        page.locator("div").filter(has_text=re.compile(r"^Board name$")).get_by_role("button").click()
        page.get_by_role("button", name="Continue").click()

    with allure.step("Открытие Board"):
        expect(page.get_by_role("button", name="Open board")).to_be_visible(timeout=10000)
        page.get_by_role("button", name="Open board").click()

    with allure.step("Проверка Board в сайдбаре"):
        expect(page.get_by_role("link", name=_BOARD_NAME)).to_be_visible(timeout=10000)

    # === TASK ===
    with allure.step(f"Создание Task: {_TASK_NAME}"):
        page.get_by_role("link", name=_BOARD_NAME).click()
        page.get_by_role("button", name="Add task").first.click()
        page.get_by_role("textbox", name="Task name...").fill(_TASK_NAME)
        page.locator("#board-card-create").get_by_role("button", name="Add task").click()

    with allure.step("Проверка Task на доске"):
        expect(page.get_by_text(_TASK_NAME)).to_be_visible(timeout=10000)
        page.keyboard.press("Escape")  # закрываем форму создания задачи
        page.wait_for_timeout(1000)    # ждём прогрузку карточки задачи

    with allure.step("Сравнение скриншота доски"):
        page.mouse.move(640, 400)  # убираем hover
        page.wait_for_timeout(500)

        dynamic_masks = [
            page.locator('[class*="MemberAvatar-module_Root"]'),
            page.locator('[class*="HeaderSpaceSelector-module_Icon"]'),   # иконка Space в хедере (рандомный цвет)
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
        assert_snapshot(screenshot, name="board_with_task.png", threshold=1.5)
