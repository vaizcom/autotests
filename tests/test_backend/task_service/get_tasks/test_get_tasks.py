import pytest
import allure

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

# Базовые smoke-тесты

@allure.title("GetTasks: базовый смоук — успешный ответ и массив tasks")
@allure.description("Проверка, что эндпоинт возвращает 200 и тело с полем tasks (массив).")
def test_get_tasks_minimal(owner_client, board_with_tasks, main_space):
    with allure.step("Выполнить POST /GetTasks без доп. параметров"):
        response = owner_client.post(**get_tasks_endpoint(board=board_with_tasks, space_id=main_space))
    with allure.step("Проверить статус и контракт ответа"):
        assert response.status_code == 200
        data = response.json()['payload']
        assert "tasks" in data and isinstance(data["tasks"], list)

