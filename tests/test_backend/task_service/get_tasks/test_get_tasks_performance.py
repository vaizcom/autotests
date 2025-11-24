import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.title("Проверка производительности запроса")
def test_get_tasks_response_time(request, board_with_10000_tasks, main_space):
    """Проверяет что запрос выполняется за разумное время"""
    import time

    client = request.getfixturevalue('owner_client')

    start_time = time.time()

    with allure.step("owner_client: вызвать GetTasks"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_10000_tasks))

    end_time = time.time()
    response_time = end_time - start_time

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step(f"Проверить время ответа (фактическое: {response_time:.2f}s)"):
        # Разумный лимит времени ответа - 10 секунд
        assert response_time < 10.0, f"Запрос выполнялся слишком долго: {response_time:.2f}s"

