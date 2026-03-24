import allure
import pytest

from test_backend.data.endpoints.Space.assert_space_payload import assert_space_payload
from test_backend.data.endpoints.Space.space_endpoints import get_space_endpoint
from test_backend.task_service.utils import get_client

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Space Service")
@allure.suite("Get space access")
@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 200),
        ('foreign_client', 400)
    ],
    ids=['owner', 'manager', 'member', 'guest','no_access_to_space'],
)
def test_get_space(request, main_space, client_fixture, expected_status):
    """
    Тест проверки получения space под разными ролями с валидацией набора полей и типов.
    """
    allure.dynamic.title(
        f"Get space: клиент={client_fixture}, ожидаемый статус={expected_status}")

    client = get_client(request, client_fixture)

    with allure.step("Получение space"):
        response = client.post(**get_space_endpoint(space_id=main_space))

    # Проверяем статус ответа
    with allure.step(f"Проверка статус-кода: ожидаем {expected_status}"):
        assert response.status_code == expected_status, response.text

        # Если запрос успешен, валидируем структуру и типы
        if response.status_code == 200:
            with allure.step("Проверяем содержимое ответа"):
                body = response.json()

                # Верхний уровень ответа
                assert "payload" in body and isinstance(body["payload"],
                                                        dict), "Ошибка: отсутствует/некорректен ключ 'payload'"
                assert "space" in body["payload"] and isinstance(body["payload"]["space"],
                                                                 dict), "Ошибка: отсутствует/некорректен ключ 'payload.space'"
                assert "type" in body and isinstance(body["type"], str), "Ошибка: отсутствует/некорректен ключ 'type'"
                assert body[
                           "type"] == "GetSpace", f"Неверное значение поля 'type': {body['type']}, ожидается 'GetSpace'"

                space = body["payload"]["space"]

                # Вызываем переиспользуемый валидатор схемы, передавая ожидаемый ID
                assert_space_payload(space, expected_space_id=main_space)

        else:
            # Проверка ответа с ошибкой
            error_response = response.json().get("error", {})
            assert 'code' in error_response, "В ответе об ошибке отсутствует ключ 'code'"
            assert error_response['code'] == 'MemberDidNotFound'

