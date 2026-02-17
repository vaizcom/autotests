import time
import allure
import requests
import pytest

from config.settings import API_URL
from test_backend.data.endpoints.User.register_endpoint import register_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Auth Service")
@allure.suite("Registration")
@allure.sub_suite("Missing field")
@pytest.mark.parametrize("field_to_remove", [
    "email",
    "password",
    "fullName",
    "termsAccepted"
], ids=["missing_email", "missing_password", "missing_fullname", "missing_terms"])
def test_register_missing_field(field_to_remove, base_url=API_URL):
    """
    Универсальный тест на проверку обязательности полей при регистрации.
    Удаляет указанное поле из валидного запроса и ожидает ошибку 400.
    """
    allure.dynamic.title(f"Register: Отказ при отсутствии поля '{field_to_remove}'")

    timestamp = int(time.time())

    with allure.step("Подготовка валидного набора данных"):
        endpoint_data = register_endpoint(
            email=f"missing_{field_to_remove}_{timestamp}@gmail.com",
            password="validPass123",
            full_name=f"User {timestamp}",
            terms_accepted=True
        )

    with allure.step(f"Удаление обязательного поля: {field_to_remove}"):
        payload = endpoint_data['json']

        # Проверяем наличие ключа перед удалением, чтобы тест не упал с KeyError
        # если структура endpoint_data изменится
        if field_to_remove in payload:
            del payload[field_to_remove]
        else:
            pytest.fail(f"Тестовое поле '{field_to_remove}' не найдено в базовом запросе. "
                        f"Доступные поля: {list(payload.keys())}")

    with allure.step("Отправка запроса"):
        url = f"{base_url.rstrip('/')}{endpoint_data['path']}"
        resp = requests.post(url, json=payload, headers=endpoint_data['headers'])

    with allure.step("Проверка кода ответа (400 Bad Request)"):
        assert resp.status_code == 400, \
            f"Ожидался статус 400, но получен {resp.status_code}. Ответ: {resp.text}"

    with allure.step(f"Проверка упоминания поля '{field_to_remove}' в ошибке"):
        resp_json = resp.json()
        error_text = str(resp_json).lower()

        # Приводим имя поля к нижнему регистру для поиска (fullName -> fullname)
        expected_field_mention = field_to_remove.lower()

        assert expected_field_mention in error_text, \
            f"Текст ошибки не содержит упоминания пропущенного поля '{field_to_remove}'"