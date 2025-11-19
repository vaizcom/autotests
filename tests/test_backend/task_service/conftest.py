import random
from datetime import datetime

import pytest

from tests.test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint
from test_backend.task_service.utils import get_client, create_task, get_random_type_id, get_random_group_id, \
    get_current_timestamp, get_due_end, get_priority, get_assignee


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
        task_name = kwargs.get(
            "name") or f"Create task клиент={client_fixture}, дата={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        random_type_id = kwargs.get("types") or [get_random_type_id(client, main_board, main_space)]
        random_group_id = kwargs.get("group") or get_random_group_id(client, main_board, main_space)
        current_timestamp = kwargs.get("due_start") or get_current_timestamp()
        due_end = kwargs.get("due_end") or get_due_end()
        priority = kwargs.get("priority") if "priority" in kwargs else get_priority()
        random_member_id = kwargs.get("assignees") or [get_assignee(client, main_space)]
        get_random_complete = kwargs.get("completed") if "completed" in kwargs else random.choice([True, False])

        if "milestones" in kwargs:
            milestones = kwargs["milestones"]
        else:
            milestones = None

        parent_task = kwargs["parent_task"] if "parent_task" in kwargs else None
        index_task = kwargs["index"] if "index" in kwargs else None

        # Формирование payload с обязательными и опциональными параметрами
        payload = create_task_endpoint(
            space_id=main_space,
            board=main_board,
            name=task_name,
            types=random_type_id,
            assignees=random_member_id,
            due_start=current_timestamp,
            due_end=due_end,
            priority=priority,
            completed=get_random_complete,
            group=random_group_id,
            milestones=milestones,
            parent_task=parent_task,
            index=index_task,
        )

        # Отправка запроса на создание задачи
        response = create_task(client, payload)
        response.raise_for_status()

        # Логика возврата созданной задачи
        task = response.json()["payload"]["task"]
        return task

    return _create_task