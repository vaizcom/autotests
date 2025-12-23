import allure
import pytest

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
            assert "payload" in body and isinstance(body["payload"], dict), "Ошибка: отсутствует/некорректен ключ 'payload'"
            assert "space" in body["payload"] and isinstance(body["payload"]["space"], dict), "Ошибка: отсутствует/некорректен ключ 'payload.space'"
            assert "type" in body and isinstance(body["type"], str), "Ошибка: отсутствует/некорректен ключ 'type'"
            assert body["type"] == "GetSpace", f"Неверное значение поля 'type': {body['type']}, ожидается 'GetSpace'"

            space = body["payload"]["space"]

            # Ожидаемые ключи и типы
            expected_schema = {
                "_id": str,
                "name": str,
                "avatar": str,
                "avatarMode": int,
                "color": dict,
                "createdAt": str,
                "creator": str,
                "isForeign": bool,
                "plan": str,
                "updatedAt": str,
            }

            # Проверяем, что набор ключей совпадает ровно
            with allure.step("Проверка полного совпадения набора полей space"):
                actual_keys = set(space.keys())
                expected_keys = set(expected_schema.keys())
                missing = expected_keys - actual_keys
                extra = actual_keys - expected_keys
                assert not missing, f"Отсутствуют обязательные поля: {sorted(missing)}"
                assert not extra, f"Найдены лишние поля: {sorted(extra)}"

            # Проверка типов по схеме
            with allure.step("Проверка типов данных всех полей space"):
                for field, expected_type in expected_schema.items():
                    value = space[field]
                    assert isinstance(value, expected_type), (
                        f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
                    )

            # Дополнительные уточнения для поля 'color'
            with allure.step("Дополнительные проверки содержимого поля 'color'"):
                color_data = space["color"]
                assert "color" in color_data and isinstance(color_data["color"], str), "Ошибка: отсутствует/некорректен ключ 'color.color'"
                assert "isDark" in color_data and isinstance(color_data["isDark"], bool), "Ошибка: отсутствует/некорректен ключ 'color.isDark'"

            # Несколько бизнес-проверок значения (по возможности стабильных)
            with allure.step("Бизнес-проверки стабильных значений"):
                assert space["_id"] == main_space, "Ошибка: неверное значение поля '_id' для space"

    else:
        error_response = response.json()["error"]
        assert error_response['code'] == 'MemberDidNotFound'

