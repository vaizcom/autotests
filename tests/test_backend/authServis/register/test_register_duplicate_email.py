import time
import allure
import requests

from config.settings import API_URL
from test_backend.data.endpoints.User.register_endpoint import register_endpoint
import pytest

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Auth Service")
@allure.suite("Registration")
def test_register_duplicate_email(base_url=API_URL):
    """
    Тест на невозможность регистрации двух пользователей с одинаковым email.
    """
    allure.dynamic.title("Register: Ошибка при регистрации существующего email")

    # Общие данные
    timestamp = int(time.time())
    shared_email = f"duplicate_{timestamp}@gmail.com"
    password = "123456"

    # --- ШАГ 1: Регистрация первого пользователя ---
    with allure.step("1. Регистрация первичного пользователя"):
        user1_name = f"user1_{timestamp}"
        endpoint_data_1 = register_endpoint(
            email=shared_email,
            password=password,
            full_name=user1_name,
            terms_accepted=True
        )
        url = f"{base_url.rstrip('/')}{endpoint_data_1['path']}"

        resp1 = requests.post(url, json=endpoint_data_1['json'], headers=endpoint_data_1['headers'])
        assert resp1.status_code == 200, f"Первичная регистрация не удалась. Статус: {resp1.status_code}"

    # --- ШАГ 2: Попытка регистрации второго пользователя с тем же email ---
    with allure.step("2. Попытка повторной регистрации с тем же email"):
        user2_name = f"user2_{timestamp}"
        endpoint_data_2 = register_endpoint(
            email=shared_email,  # Тот же email
            password=password,
            full_name=user2_name,
            terms_accepted=True
        )

        resp2 = requests.post(url, json=endpoint_data_2['json'], headers=endpoint_data_2['headers'])

    # --- ШАГ 3: Проверки ---
    with allure.step("Проверка отказа в регистрации"):
        assert resp2.status_code == 400, \
            f"Ожидался статус 400, но получен {resp2.status_code}. Ответ: {resp2.text}"

    with allure.step("Валидация тела ошибки (EmailAlreadyExists)"):
        resp_json = resp2.json()
        error_data = resp_json.get('error')

        assert error_data is not None, "В ответе отсутствует поле error"
        assert error_data.get('code') == "InvalidForm", "Код ошибки не InvalidForm"

        # Поиск конкретной ошибки поля
        fields = error_data.get('fields', [])
        email_errors = [f for f in fields if f.get('name') == 'email']

        assert len(email_errors) > 0, "Не найдена ошибка для поля email"
        assert "EmailAlreadyExists" in email_errors[0].get('codes', []), \
            f"Ожидался код ошибки 'EmailAlreadyExists', получено: {email_errors[0].get('codes')}"