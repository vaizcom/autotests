from datetime import datetime

import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint
from test_backend.task.utils import get_client, create_task


@pytest.fixture
def create_task_in_main(request, main_space, main_board, main_project):
    """
    Фикстура для создания задачи в main_board.
    :param request: фикстура для доступа к другим данным через request.getfixturevalue.
    :param main_space: ID основного пространства.
    :param main_board: ID основной борды (обязательный параметр).
    :param main_project: ID основного проекта.
    :return: функция для создания задачи с заданным payload.
    """

    def _create_task(client_fixture, **kwargs):
        """
        Создает задачу в main_board с кастомными параметрами из kwargs.
        :param client_fixture: имя фикстуры для получения клиента (например, 'owner_client').
        :param kwargs: опциональные параметры для задачи.
        """
        # Получение клиента
        client = get_client(request, client_fixture)

        # Формирование payload с обязательными и опциональными параметрами
        payload = create_task_endpoint(
            space_id=main_space,
            board=main_board,
            name=kwargs.get("name", f"Default Task {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"),
            types=kwargs.get("types", ["6866731185fb8d104544e82b"]),
            assignees=kwargs.get("assignees", ["6866309d85fb8d104544a620"]),
            due_start=kwargs.get("due_start", "2025-09-19T14:47:17.596+00:00"),
            due_end=kwargs.get("due_end", "2026-09-19T14:47:17.596+00:00"),
            priority=kwargs.get("priority", 3),
            completed=kwargs.get("completed", False),
            group=kwargs.get("group", "6866731185fb8d104544e828"),
            milestones=kwargs.get("milestones", ["68d5189654c332d6918a9b52"]),
            parent_task=kwargs.get("parent_task", None),
            index=kwargs.get("index", 1),
        )

        # Отправка запроса на создание задачи
        response = create_task(client, payload)
        response.raise_for_status()

        # Логика возврата созданной задачи
        task = response.json()["payload"]["task"]
        return task

    return _create_task