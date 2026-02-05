import random
from datetime import datetime
from typing import List

import pytest

from tests.test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, delete_task_endpoint, \
    edit_task_custom_field_endpoint
from test_backend.task_service.utils import get_client, create_task, get_random_type_id, get_random_group_id, \
    get_current_timestamp, get_due_end, get_priority, get_assignee


@pytest.fixture
def create_task_in_main(request, main_space, main_board, main_project):
    """
    Фикстура для создания задачи в main_board с установленными параметрами.
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
        random_member_id = kwargs.get("assignees") or get_assignee(client, main_space)
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

@pytest.fixture
def create_30_tasks(owner_client, main_space, main_board):
    """
    Фикстура создаёт N задач и гарантированно удаляет их по завершении теста.
    Использование:
        task_ids = create_30_tasks()           # по умолчанию 30 задач
        task_ids = create_30_tasks(count=10)   # создать 10 задач
    """
    created_ids: List[str] = []

    def _factory(count: int = 30) -> List[str]:
        nonlocal created_ids
        created_ids = []
        for i in range(count):
            title = f"Multiple Edit Tasks #{i + 1}"
            resp = owner_client.post(
                **create_task_endpoint(space_id=main_space, board=main_board, name=title, completed=False))
            resp.raise_for_status()
            body = resp.json()
            task = (body.get("payload") or {}).get("task") or body.get("task") or {}
            task_id = task.get("_id") or task.get("id")
            assert task_id, f"Не удалось получить _id созданной задачи: {body!r}"
            created_ids.append(task_id)
        return created_ids

    yield _factory

    # Teardown: удаление созданных задач
    if created_ids:
        for tid in created_ids:
            try:
                resp = owner_client.post(**delete_task_endpoint(task_id=tid, space_id=main_space))
                # допускаем 2xx/404 (если задача уже удалена в тесте)
                if resp.status_code >= 400 and resp.status_code != 404:
                    pass
            except Exception:
                pass


@pytest.fixture
def make_task_in_main(owner_client, main_space, main_board):
    """
    Фикстура-конструктор задачи.
    Возвращает функцию create -> dict с данными созданной задачи.
    В body передаются только необходимые для теста поля. После использования задача удаляется.
    """
    created_ids = []

    def _create_task(body_overrides: dict):
        body = {
            "space_id": main_space,
            "board": main_board
        }
        # объединим остальные поля в create_task_endpoint через kwargs
        resp = owner_client.post(**create_task_endpoint(**body, **body_overrides))
        assert resp.status_code == 200, resp.text
        task = resp.json()["payload"]["task"]
        created_ids.append(task["_id"])
        return task

    yield _create_task

    # Teardown: удаление созданных задач
    if created_ids:
        for tid in created_ids:
            try:
                resp = owner_client.post(**delete_task_endpoint(task_id=tid, space_id=main_space))
                # допускаем 2xx/404 (если задача уже удалена в тесте)
                if resp.status_code >= 400 and resp.status_code != 404:
                    pass
            except Exception:
                pass

def _update_custom_field(client, space_id, task_id, field_id, value):
    """
    Вспомогательная функция для обновления значения кастомного поля.
    """
    return client.post(**edit_task_custom_field_endpoint(
        space_id=space_id,
        task_id=task_id,
        field_id=field_id,
        value=value
    ))