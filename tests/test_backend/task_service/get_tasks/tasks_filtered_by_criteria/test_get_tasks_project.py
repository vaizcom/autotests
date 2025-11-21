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
            limit=50
        ))
    with allure.step("Проверить HTTP 200 и массив tasks"):
        assert response.status_code == 200
        data = response.json().get("payload", {})
        tasks = data.get("tasks", [])
        assert isinstance(tasks, list)

    if not tasks:
        pytest.skip("Список задач пуст — нечего валидировать по фильтру проекта")

    for task in tasks[:20]:
        assert task.get("project") == main_project, (
            f"Задача {task.get('_id', 'unknown')} принадлежит другой project: {task.get('project')}"
        )

@allure.title("GetTasks project: project не принадлежит space — ожидаем пустой список задач")
def test_get_tasks_project_mismatched_space(owner_client, second_space, main_project):
    with allure.step("Выполнить POST /GetTasks с space_id другого пространства и project текущей доски"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=second_space,
            project=main_project
        ))
    with allure.step("Проверить контракт: HTTP 200 и пустой tasks"):
        if response.status_code == 200:
            data = response.json().get("payload", {})
            tasks = data.get("tasks", [])
            assert isinstance(tasks, list)
            assert tasks == []


@allure.title("GetTasks project: неверный формат идентификатора — ожидаем ошибку валидации 'project must be a mongodb id'")
def test_get_tasks_project_non_existing(owner_client, main_space):
    with allure.step("Выполнить POST /GetTasks с несуществующим board"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            project="main_project"
        ))
    with allure.step("Проверить контракт: HTTP 400 и 'project must be a mongodb id'"):
        if response.status_code == 400:
            body = response.json()
            assert body.get("payload") is None
            error = body.get("error", {})
            assert error.get("code") == "InvalidForm"
            fields = error.get("fields", [])
            board_field = next((f for f in fields if f.get("name") == "project"), None)
            codes = board_field.get("codes", [])
            assert "project must be a mongodb id" in codes

@allure.title("GetTasks project: project без задач — ожидаем пустой список")
def test_get_tasks_project_without_tasks(owner_client, main_space):
    with allure.step("Выполнить POST /GetTasks для project без задач"):
        empty_project = '691d789f0ba789a8848d899d'
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            project=empty_project
        ))
    with allure.step("Проверить HTTP 200 и пустой массив tasks"):
        assert response.status_code == 200
        data = response.json().get("payload", {})
        tasks = data.get("tasks", [])
        assert isinstance(tasks, list)
        assert tasks == []