import pytest
import allure
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.title("GetTasks limit: Возвращает abs(limit) тасок (если данных достаточно)")
@pytest.mark.parametrize("expected_limit", [1, 100])
def test_get_tasks_limit(owner_client, main_space, board_with_10000_tasks, expected_limit):
    allure.dynamic.title(f"GetTasks limit: {expected_limit}")

    with allure.step(f"Выполнить запрос с limit={expected_limit}"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_10000_tasks,
            limit=expected_limit
        ))

    with allure.step("Проверить HTTP 200 и размер выборки"):
        assert response.status_code == 200, f"Ожидался 200, получено: {response.status_code}"
        tasks = response.json().get("payload", {}).get("tasks", [])
        assert isinstance(tasks, list), "payload.tasks должен быть массивом"
        assert len(tasks) == abs(expected_limit), f"Количество задач превышает limit: {len(tasks)} > {expected_limit}"


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.title("GetTasks limit: равен 0 —  означает отсутствие ограничения, выводится весь список")
def test_get_tasks_limit_zero(owner_client, main_space, board_with_tasks):
    with allure.step("Выполнить запрос с limit=0"):
        response = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            limit=0
        ))

    with allure.step("Проверить HTTP 200 и поведение при нуле"):
        assert response.status_code == 200
        tasks = response.json().get("payload", {}).get("tasks", [])
        assert isinstance(tasks, list)
        assert len(tasks) != 0


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.title("GetTasks limit: превышает доступное кол-во задач — возвращается не больше фактического")
def test_get_tasks_limit_more_than_available(owner_client, main_space, board_with_10000_tasks):
    with allure.step("Получить фактическое число задач без limit"):
        resp_all = owner_client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_10000_tasks))
        assert resp_all.status_code == 200
        all_tasks = resp_all.json().get("payload", {}).get("tasks", [])
        total = len(all_tasks)

    with allure.step("Выполнить запрос с limit больше фактического"):
        expected_limit = total + 10 if total > 0 else 10
        resp_limited = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_10000_tasks,
            limit=expected_limit
        ))

    with allure.step("Проверить, что вернулось не больше фактического числа задач"):
        assert resp_limited.status_code == 200
        tasks = resp_limited.json().get("payload", {}).get("tasks", [])
        assert len(tasks) == total, f"Ожидалось {total} задач, получено: {len(tasks)}"