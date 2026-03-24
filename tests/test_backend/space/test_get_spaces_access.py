import allure
import pytest

from test_backend.data.endpoints.Space.assert_space_payload import assert_space_payload
from test_backend.data.endpoints.Space.space_endpoints import get_spaces_endpoint
from test_backend.task_service.utils import get_client

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Space Service")
@allure.suite("Get spaces access")
@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 200)
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_get_spaces(request, main_space, client_fixture, expected_status):
    """
    Тест проверки получения списка spaces под разными ролями с валидацией набора полей и типов.
    """
    allure.dynamic.title(
        f"Get spaces: клиент={client_fixture}, ожидаемый статус={expected_status}"
    )
    client = get_client(request, client_fixture)
    with allure.step("Получение списка spaces"):
        response = client.post(**get_spaces_endpoint())
    # Проверяем статус ответа
    with allure.step(f"Проверка статус-кода: ожидаем {expected_status}"):
        assert response.status_code == expected_status, response.text
    if response.status_code == 200:
        with allure.step("Проверяем содержимое ответа"):
            body = response.json()
            assert "payload" in body and isinstance(body["payload"],
                                                    dict), "Ошибка: отсутствует/некорректен ключ 'payload'"
            assert "spaces" in body["payload"] and isinstance(body["payload"]["spaces"],
                                                              list), "Ошибка: отсутствует/некорректен ключ 'payload.spaces'"
            assert "type" in body and isinstance(body["type"], str), "Ошибка: отсутствует/некорректен ключ 'type'"
            assert body["type"] == "GetSpaces", f"Неверное значение поля 'type': {body['type']}, ожидается 'GetSpaces'"

            spaces = body["payload"]["spaces"]

            for space in spaces:
                # Валидация каждого space в списке через вынесенный валидатор
                assert_space_payload(space)

    else:
        # Для случаев, когда статус не 200, проверяем структуру ошибки
        error_response = response.json().get("error", {})
        assert 'code' in error_response, f"В ответе об ошибке отсутствует ключ 'code': {response.text}"
        assert 'message' in error_response, f"В ответе об ошибке отсутствует ключ 'message': {response.text}"