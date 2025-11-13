import pytest
import allure
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.title("GetTasks skip: skip=0, limit=20 → возвращаются первые 20")
def test_get_tasks_skip_zero(owner_client, main_space, board_with_tasks):
    with allure.step("Выполнить запрос с limit=20 и skip=0"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            limit=20,
            skip=0
        ))

    with allure.step("Проверить HTTP 200 и размер выборки 20"):
        assert response.status_code == 200
        tasks = response.json().get("payload", {}).get("tasks", [])
        assert isinstance(tasks, list)
        assert len(tasks) == 20

@allure.title("GetTasks skip: skip=5, limit=20 → элементы начинаются с 5-го")
def test_get_tasks_skip_five(owner_client, main_space, board_with_tasks):
    with allure.step("Получить опорный список задач без skip (большой limit)"):
        resp_all = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            limit=100
        ))
        assert resp_all.status_code == 200
        all_tasks = resp_all.json().get("payload", {}).get("tasks", [])
        assert isinstance(all_tasks, list)
        assert len(all_tasks) == 100

    with allure.step("Выполнить запрос с limit=20 и skip=5"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            limit=20,
            skip=5
        ))

    with allure.step("Проверить HTTP 200, первый элемент со смещением равным skip=5"):
        assert response.status_code == 200
        tasks = response.json().get("payload", {}).get("tasks", [])
        assert isinstance(tasks, list)
        if all_tasks[5:6]:
            assert tasks[:1] == all_tasks[5:6], "Первый элемент должен совпадать с элементом под индексом 5 полного списка"

@allure.title("GetTasks skip: негатив — skip не число (строка)")
@allure.description("Ожидаем валидационную ошибку при передаче skip='five'")
def test_get_tasks_skip_not_number_string(owner_client, main_space, board_with_tasks):
    with allure.step("Выполнить запрос с skip='five'"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            limit=20,
            skip="five"
        ))
    with allure.step("Проверить HTTP 400 и описание ошибки"):
        assert response.status_code == 400, "Ожидался код 400 при нечисловом skip"
        body = response.json()
        assert isinstance(body, dict)
        message = str(body)
        assert "skip must be a number conforming to the specified constraints" in message
