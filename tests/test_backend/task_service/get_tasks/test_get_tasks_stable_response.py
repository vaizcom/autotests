import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.title("Проверка стабильности ответа при множественных запросах")
def test_get_tasks_stable_response(request, board_with_tasks, main_space):
    """Проверяет что множественные запросы возвращают одинаковый результат"""
    client = request.getfixturevalue('owner_client')
    responses = []

    with allure.step("Выполнить 3 идентичных запроса"):
        for i in range(3):
            with allure.step(f"Запрос {i+1}"):
                resp = client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_tasks))
                assert resp.status_code == 200
                responses.append(resp.json())

    with allure.step("Проверить идентичность ответов(Сравнивает каждый последующий ответ с первым)"):
        first_response = responses[0]
        for i, response in enumerate(responses[1:], 2):
            assert response == first_response, f"Ответ {i} отличается от первого"