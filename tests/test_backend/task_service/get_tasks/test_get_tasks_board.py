import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.title("GetTasks board: валидная доска — успешный ответ и задачи этой доски")
def test_get_tasks_board_valid(owner_client, main_space, board_with_tasks):
    with allure.step("Выполнить POST /GetTasks с валидными space_id и board"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks
        ))
    with allure.step("Проверить HTTP 200 и массив tasks"):
        assert response.status_code == 200
        data = response.json().get("payload", {})
        tasks = data.get("tasks", [])
        assert isinstance(tasks, list)

@allure.title("GetTasks board: доска не принадлежит space — ожидаем пустой список задач")
def test_get_tasks_board_mismatched_space(owner_client, second_space, board_with_tasks):
    with allure.step("Выполнить POST /GetTasks с space_id другого пространства и board текущей доски"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=second_space,
            board=board_with_tasks
        ))
    with allure.step("Проверить контракт: либо HTTP 200 и пустой tasks"):
        if response.status_code == 200:
            data = response.json().get("payload", {})
            tasks = data.get("tasks", [])
            assert isinstance(tasks, list)
            assert tasks == []


@allure.title("GetTasks board: неверный формат идентификатора — ожидаем ошибку валидации 'board must be a mongodb id'")
def test_get_tasks_board_non_existing(owner_client, main_space):
    with allure.step("Выполнить POST /GetTasks с несуществующим board"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board="main_board_id"
        ))
    with allure.step("Проверить контракт: либо HTTP 200 и пустой tasks, либо 404"):
        if response.status_code == 400:
            body = response.json()
            assert body.get("payload") is None
            error = body.get("error", {})
            assert error.get("code") == "InvalidForm"
            fields = error.get("fields", [])
            board_field = next((f for f in fields if f.get("name") == "board"), None)
            codes = board_field.get("codes", [])
            assert "board must be a mongodb id" in codes

@allure.title("GetTasks board: доска без задач — ожидаем пустой список")
def test_get_tasks_board_without_tasks(owner_client, main_space):
    with allure.step("Выполнить POST /GetTasks для доски без задач"):
        empty_board = '691ae8ff4bfde6405da01137'
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=empty_board
        ))
    with allure.step("Проверить HTTP 200 и пустой массив tasks"):
        assert response.status_code == 200
        data = response.json().get("payload", {})
        tasks = data.get("tasks", [])
        assert isinstance(tasks, list)
        assert tasks == []
