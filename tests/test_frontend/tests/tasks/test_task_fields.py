import re

import allure
import pytest
import pytest_check as check
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings

pytestmark = [pytest.mark.frontend]

_SPACE_NAME = settings.AUTOTEST_SPACE_NAME
_PROJECT_NAME = settings.AUTOTEST_PROJECT_NAME
_BOARD_NAME = "temp_board"
_TASK_NAME = "temp_task"
_SUBTASK_NAME = "Test subtask"
_DESCRIPTION = "Test description"
_COMMENT = "Test comment"
_MILESTONE_NAME = "Test milestone"
_BLOCKER_NAME = "Blocker task"
_BLOCKING_NAME = "Blocking task"
_CUSTOM_TEXT_VALUE = "Test value"


@pytest.mark.skipif(settings.FRONTEND_STAND == "prod", reason="Создание сущностей тестируется только на dev")
@allure.parent_suite("Frontend")
@allure.suite("Tasks")
@allure.title("Create task and fill fields")
def test_create_and_fill_task(page: Page, cleanup_board, assert_snapshot):
    """
    Проверяет создание борды и задачи через UI с заполнением полей:
    статус, приоритет, исполнитель, тип, описание, подзадача, комментарий.
    Борда удаляется через API в teardown. Тест не запускается на проде.
    """

    # === НАВИГАЦИЯ — переход в нужный Space и Project ===
    with allure.step(f"Открытие {_SPACE_NAME}"):
        page.goto(f"{settings.BASE_URL}/")
        expect(page.get_by_role("link", name="Home")).to_be_visible(timeout=15000)
        page.locator('[class*="HeaderSpaceSelector-module_Inner"]').first.click()
        page.get_by_label("Menu", exact=True).get_by_text(_SPACE_NAME).click()
        page.wait_for_url(lambda url: settings.BASE_URL in url, timeout=10000)
        space_id = page.url.replace(settings.BASE_URL, "").strip("/").split("/")[0]

    with allure.step(f"Открытие {_PROJECT_NAME}"):
        page.locator("span").filter(has_text=_PROJECT_NAME).get_by_role("link").click()
        expect(page.get_by_text("Add board")).to_be_visible(timeout=10000)

    # === БОРДА — создаём временную борду, удалится в teardown ===
    with allure.step(f"Создание Board: {_BOARD_NAME}"):
        page.get_by_text("Add board").click()
        page.get_by_role("button", name="Start creating").click()
        continue_btn = page.get_by_role("button", name="Continue")
        expect(continue_btn).to_be_visible(timeout=10000)
        continue_btn.click()
        page.get_by_role("textbox", name="Board name").fill(_BOARD_NAME)
        page.get_by_role("button", name="Create board").click()
        # Регистрируем cleanup сразу после создания — teardown найдёт борду по имени
        cleanup_board.append({"board_name": _BOARD_NAME, "space_id": space_id})
        page.get_by_role("button", name="Continue").click()

        # # Добавление участника из спейса
        # page.get_by_role("textbox", name="Begin typing to search").fill(settings.AUTOTEST_MEMBER_EMAIL)
        # page.get_by_role("textbox", name="Begin typing to search").press("Enter")
        # page.get_by_role("button", name="Add members").click()

    with allure.step("Открытие Board"):
        expect(page.get_by_role("button", name="Open board")).to_be_visible(timeout=10000)
        page.get_by_role("button", name="Open board").click()
        expect(page.get_by_role("button", name="Add task").first).to_be_visible(timeout=10000)

    # === ЗАДАЧА — создаём задачу и открываем в сайдбаре ===
    with allure.step(f"Создание Task: {_TASK_NAME}"):
        page.get_by_role("button", name="Add task").first.click()
        expect(page.get_by_role("textbox", name="Task name...")).to_be_visible(timeout=5000)
        page.get_by_role("textbox", name="Task name...").fill(_TASK_NAME)
        page.locator("#board-card-create").get_by_role("button", name="Add task").click()

    with allure.step("Открытие Task в сайдбаре"):
        task_card = page.get_by_role("button").filter(
            has_text=re.compile(r"[A-Z]+-\d+")
        ).filter(has_text=_TASK_NAME)
        expect(task_card).to_be_visible(timeout=10000)
        task_card.click()
        expect(page.get_by_role("heading", name=_TASK_NAME)).to_be_visible(timeout=10000)

    # === ПОЛЯ — заполняем все поля задачи, soft assertions чтобы не стопиться на первом падении ===
    def soft_step(name, fn):
        try:
            fn()
        except Exception as e:
            check.fail(f"{name}: {e}")

    with allure.step("Завершение задачи (Complete)"):
        soft_step("Complete", lambda: page.locator('[class*="_Check_"]').first.click())

    with allure.step("Приоритет: Medium"):
        soft_step("Приоритет", lambda: (
            page.get_by_role("button", name="Priority Select priority").click() or
            page.get_by_text("Medium").click()
        ))

    with allure.step("Исполнитель (assign первый в дропдауне)"):
        def assign():
            page.get_by_role("button", name="Assign Not assigned").click()
            page.locator('.szh-menu-container [class*="SelectFlySearch-module_ItemText"]').first.click()
            page.locator(".FlyBlock-module_Overlay_k4A8s").click()
        soft_step("Исполнитель", assign)

    with allure.step("Тип: Green"):
        soft_step("Тип", lambda: (
            page.get_by_role("button", name="Types Select type").click() or
            page.get_by_text("Green").click()
        ))

    with allure.step(f"Описание: {_DESCRIPTION}"):
        soft_step("Описание", lambda: (
            page.locator('[id^="editor-content-"]').get_by_role("paragraph").click() or
            page.locator(".tiptap").first.fill(_DESCRIPTION)
        ))

    with allure.step(f"Подзадача: {_SUBTASK_NAME}"):
        soft_step("Подзадача", lambda: (
            page.get_by_role("textbox", name="Enter subtask name").fill(_SUBTASK_NAME) or
            page.keyboard.press("Enter")
        ))

    with allure.step("Майлстоун"):
        def add_milestone():
            page.get_by_role("button", name="Milestones Select milestones").click()
            page.get_by_role("menuitem", name="Create milestone").locator("div").first.click()
            page.get_by_role("textbox", name="Type name").fill(_MILESTONE_NAME)
            page.get_by_role("button", name="Add", exact=True).click()
        soft_step("Майлстоун", add_milestone)

    with allure.step("Дата"):
        def add_date():
            page.get_by_role("button", name="Dates No dates set").click()
            date_input = page.get_by_placeholder(re.compile(r"\d{2}\.\d{2}\.\d{4}")).first
            date_input.fill("10.08.2030")
            page.get_by_role("button", name="Apply").click()
        soft_step("Дата", add_date)

    with allure.step("Блокер и блокинг"):
        def add_blockers():
            page.get_by_role("textbox", name="Add blocker").fill(_BLOCKER_NAME)
            page.get_by_role("button", name=re.compile(r"Blockers.*Create task")).get_by_role("button").click()
            # Ждём пока блокер создастся и появится поле blocking
            expect(page.get_by_role("textbox", name="Add blocking")).to_be_visible(timeout=10000)
            page.get_by_role("textbox", name="Add blocking").fill(_BLOCKING_NAME)
            page.get_by_role("button", name=re.compile(r"Blocking.*Create task")).get_by_role("button").click()
        soft_step("Блокер и блокинг", add_blockers)

    with allure.step("Кастомное поле Text"):
        def add_custom_text():
            page.locator("div").filter(has_text=re.compile(r"^Add new field$")).nth(2).click()
            page.get_by_role("menuitem", name="Text").click()
            page.get_by_role("button", name="Text").click()
            page.get_by_role("textbox", name="Empty").fill(_CUSTOM_TEXT_VALUE)
            page.keyboard.press("Escape")
        soft_step("Кастомное поле Text", add_custom_text)

    with allure.step(f"Комментарий: {_COMMENT}"):
        soft_step("Комментарий", lambda: (
            page.locator("#root").get_by_role("textbox").filter(
                has_text=re.compile(r"^$")
            ).last.fill(_COMMENT) or
            page.locator('[class*="CommentToolbar-module_Right"]').get_by_role("button").last.click()
        ))

    # === СКРИНШОТЫ — верхняя часть (поля) и нижняя (подзадача, описание, комментарий) ===
    page.add_style_tag(content='''
        span[class*="AppVersion"] {
            background-color: #FF00FF !important;
            color: transparent !important;
            display: inline-block !important;
            min-height: 14px !important;
        }
    ''')

    dynamic_masks = [
        page.locator('[class*="MemberAvatar-module_Root"]'),
        page.locator('[class*="HeaderSpaceSelector-module_Icon"]'),
        page.locator('[class*="AsideMenu-module_Footer"]'),
        page.locator('[class*="AsideNotificationsMenuItem-module_UnreadDot"]'),
        page.locator('[class*="NotificationsToggleButton-module_UnreadDot"]'),
        page.locator('[class*="TourBanner-module_Root"]'),
        page.locator('[class*="AffiliateBanner-module_Root"]'),
        page.locator('[class*="Comment-module_Date"]'),
        page.locator('[class*="TaskHrid-module"]'),
    ]

    with allure.step("Сравнение скриншота верхней части задачи"):
        expect(page.get_by_role("heading", name=_TASK_NAME)).to_be_visible(timeout=10000)
        page.get_by_role("heading", name=_TASK_NAME).scroll_into_view_if_needed()
        page.mouse.move(0, 0)
        page.wait_for_timeout(1000)

        screenshot_top = page.screenshot(mask=dynamic_masks)
        assert_snapshot(screenshot_top, name="task_fields_top.png", threshold=1.0)

    with allure.step("Сравнение скриншота нижней части задачи"):
        page.locator('[class*="CommentToolbar-module"]').first.scroll_into_view_if_needed()
        page.mouse.move(640, 400)
        page.wait_for_timeout(1000)

        screenshot_bottom = page.screenshot(mask=dynamic_masks)
        assert_snapshot(screenshot_bottom, name="task_fields_bottom.png", threshold=1.0)
