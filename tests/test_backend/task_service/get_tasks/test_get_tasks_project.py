import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.title("GetTasks project: валидный проект — успешный ответ и массив tasks")
def test_get_tasks_project_valid(owner_client, main_space, main_project, main_board):
    with allure.step("Выполнить POST /GetTasks с валидными space_id и project"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            project=main_project,
            board=main_board
        ))
    with allure.step("Проверить HTTP 200 и массив tasks"):
        assert response.status_code == 200
        data = response.json().get("payload", {})
        tasks = data.get("tasks", [])
        assert isinstance(tasks, list)
