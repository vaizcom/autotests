import random

import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint, delete_task_endpoint
from test_backend.task.utils import get_client

pytestmark = [pytest.mark.backend]

@allure.title("Проверка удаление всех задач на доске")
def test_delete_all_tasks_on_main_board(request, owner_client, main_space, main_board, create_task_in_main):
    """
    Удаляет все задачи на основной доске (main_board).
    """

    client = get_client(request, "owner_client")
    created_task_ids = []
    random_count = random.randint(1, 10)
    for i in range(1, random_count + 1):
        task = create_task_in_main(
            "owner_client",
            name=f"Random task #{i}",
        )
        created_task_ids.append(task["_id"])

    with allure.step("Запрашиваем список всех задач на main_board"):
        response = client.post(**get_tasks_endpoint(board=main_board, space_id=main_space))
        assert response.status_code == 200, f"Не удалось получить список задач: {response.text}"
        tasks = response.json()["payload"].get("tasks", [])

    if not tasks:
        allure.attach("Задачи на доске отсутствуют, нечего удалять.", "Комментарии", "text/plain")
        return

    deleted_ids = []
    for task in tasks:
        task_id = task["_id"]
        with allure.step(f"Удаляем задачу: {task_id}"):
            del_resp = client.post(**delete_task_endpoint(task_id=task_id, space_id=main_space))
            assert del_resp.status_code == 200, f"Не удалось удалить задачу {task_id}: {del_resp.text}"
            deleted_ids.append(task_id)

    allure.attach("\n".join(deleted_ids), "Удалённые ID задач", "text/plain")