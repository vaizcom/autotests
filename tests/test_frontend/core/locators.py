"""Централизованные data-test-id локаторы для фронтовых элементов.

Использование:
    from tests.test_frontend.core.locators import Header, Sidebar, Board, TaskCard

    page.get_by_test_id(Sidebar.HOME).click()
    page.get_by_test_id(Header.AVATAR).click()
    page.get_by_test_id(Board.CREATE_TASK).first.click()

Требует настройки в conftest.py:
    playwright.selectors.set_test_id_attribute("data-test-id")
"""


class Header:
    BURGER = "header.burger-button.button"
    SPACE_SELECTOR = "header.space.selector"
    SYNC_STATUS = "header.sync-status.button"
    SEARCH = "header.header-search.button"
    NOTIFICATIONS = "notifications.header-toggle-button.button"
    AVATAR = "header.profile.menu.avatar"

    @staticmethod
    def breadcrumb_project(project_id: str) -> str:
        return f"header.breadcrumbs.project.{project_id}"

    @staticmethod
    def breadcrumb_board(board_id: str) -> str:
        return f"header.breadcrumbs.board.{board_id}"


class SpaceSelector:
    """Дропдаун выбора Space (открывается по клику на Header.SPACE_SELECTOR)."""
    SETTINGS = "header.space.selector.settings"
    TEAM = "header.space.selector.team"
    BILLING = "header.space.selector.billing"
    MIGRATION = "header.space.selector.migration"
    APP_CENTER = "header.space.selector.app-center"
    CREATE = "space.space-selector.button.create"

    @staticmethod
    def space(space_id: str) -> str:
        return f"space.space-selector.item.{space_id}"


class Sidebar:
    """Сайдбар на уровне Space (Home-страница)."""
    HOME = "aside.aside-menu.list-item.home"
    FAVORITES = "aside.aside-menu.list-item.favorites"
    NOTIFICATIONS = "aside.molecules.aside-notifications-menu-item.list-item"
    DASHBOARDS = "aside.aside-menu.list-item.dashboards"
    PROJECTS = "aside.aside-menu.aside-projects-menu-item.list-item"
    ADD_PROJECT = "aside.aside-menu.aside-projects-menu-item.button.add"
    SPACE_DOCS = "aside.aside-menu.aside-docs-menu.list-item.space-docs"
    ADD_DOC = "aside.aside-menu.aside-docs-menu.button.add"
    PERSONAL_DOCS = "aside.aside-menu.aside-docs-menu.list-item.personal-docs"
    HISTORY = "aside.aside-menu.list-item.history"
    ARCHIVE = "aside.aside-menu.list-item.archive"

    @staticmethod
    def project(project_id: str) -> str:
        return f"aside.aside-menu.aside-projects-menu-item.list-item.{project_id}"


class ProjectSidebar:
    """Сайдбар внутри проекта (другой набор пунктов)."""
    BACK = "aside.molecules.aside-menu-items.button.back"
    DASHBOARDS = "aside.aside-menu.list-item.project-dashboards"
    BOARDS = "aside.aside-menu.aside-boards-menu-item.list-item"
    ADD_BOARD = "aside.aside-menu.aside-boards-menu-item.button.add"
    DOCS = "aside.aside-menu.aside-docs-menu.list-item.project-docs"
    HISTORY = "aside.aside-menu.list-item.project-history"
    SETTINGS = "aside.aside-menu.list-item.project-settings"

    @staticmethod
    def board(board_id: str) -> str:
        return f"aside.aside-menu.aside-boards-menu-item.list-item.{board_id}"


class Board:
    """Канбан-борда."""
    CREATE_TASK = "kanban-board.column.molecules.create-task-button.button"
    COLUMN_MENU = "kanban-board.column.molecules.column-header.button.menu"
    ADD_COLUMN = "kanban-board.column.new-column.button.add"


class TaskCard:
    """Карточка задачи на борде."""
    MENU = "task.task-card.button.menu"
    ADD = "task.task-card.button.add"

    @staticmethod
    def root(task_id: str) -> str:
        return f"task.task-card.root.{task_id}"

    @staticmethod
    def complete_toggle(task_id: str) -> str:
        return f"task.task-card.complete-toggle.{task_id}"


class TourBanner:
    CLOSE = "tour.banner.button.close"
    START = "tour.banner.button.start"
