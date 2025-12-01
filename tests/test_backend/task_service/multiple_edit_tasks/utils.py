from typing import List

import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint

@pytest.fixture
def tasks_ids(owner_client, main_space: str, main_board: str, count: int = 30) -> List[str]:
    """
    Вспомогательная функция: создаёт count задач на доске board_with_tasks и возвращает их _id.
    Использует create_task_endpoint. Подходит для подготовки данных в тестах.
    """
    created_ids: List[str] = []
    for i in range(count):
        title = f"Multiple_Edit_Tasks #{i+1}"
        resp = owner_client.post(**create_task_endpoint(space_id=main_space, board=main_board, name=title))
        resp.raise_for_status()
        body = resp.json()
        task = (body.get("payload") or {}).get("task") or body.get("task") or {}
        task_id = task.get("_id") or task.get("id")
        assert task_id, f"Не удалось получить _id созданной задачи из ответа: {body!r}"
        created_ids.append(task_id)
    return created_ids