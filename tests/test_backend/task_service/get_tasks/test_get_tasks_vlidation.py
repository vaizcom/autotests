import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.title("Проверка получения задач с невалидным space_id")
def test_get_tasks_invalid_space_id(owner_client, board_with_tasks):
    """Проверяет поведение при запросе с несуществующим space_id"""
    invalid_space_id = "1" * 24  # Валидный ObjectId, но не существующий

    with allure.step("owner_client: вызвать GetTasks с невалидным space_id"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=invalid_space_id, board=board_with_tasks))

    with allure.step("Проверить HTTP статус код 400"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SpaceIdNotSpecified"

@allure.title("Проверка получения задач с некорректным форматом board_id")
def test_get_tasks_invalid_format_board_id(owner_client, main_space):
    """Проверяет поведение при запросе с некорректным форматом board_id"""
    malformed_board_id = "invalid_board_id"

    with allure.step("owner_client: вызвать GetTasks с некорректным board_id = 'invalid_board_id'"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=main_space, board=malformed_board_id))

    with allure.step("Проверить HTTP 400"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "InvalidForm"
        assert resp.json()["error"]["fields"][0]["codes"] == ["board must be a mongodb id"]

@allure.title("Проверка получения задач с некорректным форматом space_id")
def test_get_tasks_invalid_format_space_id(request, board_with_tasks):
    """Проверяет поведение при запросе с некорректным форматом space_id"""
    client = request.getfixturevalue('owner_client')
    malformed_space_id = "invalid_space_id"

    with allure.step("owner_client: вызвать GetTasks с некорректным space_id='invalid_space_id'"):
        resp = client.post(**get_tasks_endpoint(space_id=malformed_space_id, board=board_with_tasks))

    with allure.step("Проверить HTTP 400"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SpaceIdNotSpecified"


@allure.title("Проверка структуры ответа при пустом списке задач")
def test_get_tasks_empty_response_structure(request, board_with_tasks, main_space):
    """Проверяет корректность структуры ответа когда задач нет"""
    # Используем клиента без доступа, чтобы гарантировать пустой список
    client = request.getfixturevalue('client_with_access_only_in_space')

    with allure.step("client_with_access_only_in_space: вызвать GetTasks"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_tasks))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Проверить структуру ответа"):
        response_json = resp.json()
        assert "payload" in response_json, "Отсутствует поле payload"

        payload = response_json["payload"]
        assert isinstance(payload, dict), "Payload должен быть объектом"
        assert "tasks" in payload, "Отсутствует поле tasks в payload"
        assert isinstance(payload["tasks"], list), "Поле tasks должно быть массивом"
        assert len(payload["tasks"]) == 0, "Список задач должен быть пустым"


@allure.title("Проверка поведения при передачи пустой строки в space_id")
def test_get_tasks_empty_string_params(request, board_with_tasks, main_space):
    """Проверяет поведение при передаче пустых строк в качестве параметров"""
    client = request.getfixturevalue('owner_client')

    with allure.step("owner_client: вызвать GetTasks с пустым space_id"):
        # Тестируем с пустым space_id в URL
        params = get_tasks_endpoint(space_id="", board=board_with_tasks)
        resp = client.post(**params)

    with allure.step("Проверить HTTP 400"):
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SpaceIdNotSpecified"


@allure.title("Проверка стабильности ответа при множественных запросах")
def test_get_tasks_consistency(request, board_with_tasks, main_space):
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


@allure.title("Проверка максимальной длины board_id")
def test_get_tasks_max_id_length(request, main_space):
    """Проверяет поведение при передаче очень длинного board_id"""
    client = request.getfixturevalue('owner_client')

    # Создаем длинный ID (больше чем must be a mongodb id)
    long_board_id = "1" * 25

    with allure.step("owner_client: вызвать GetTasks с очень длинным board_id"):
        resp = client.post(**get_tasks_endpoint(space_id=main_space, board=long_board_id))

    with allure.step("Проверить HTTP 400"):
        assert resp.status_code == 400
        assert resp.json()["error"]["fields"][0]["codes"] == ["board must be a mongodb id"]

