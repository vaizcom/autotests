import time
import allure
import requests
import pytest

from config.settings import API_URL
from test_backend.data.endpoints.User.register_endpoint import register_endpoint

pytestmark = [pytest.mark.backend]

MAX_FULL_NAME_LENGTH = 30

@allure.parent_suite("Auth Service")
@allure.suite("Registration Validation")
@pytest.mark.parametrize("fullname_value, description", [
    ("a" * (MAX_FULL_NAME_LENGTH + 1), f"Имя длиннее максимума ({MAX_FULL_NAME_LENGTH + 1} симв.)"),
    ("", "Пустое имя")
], ids=["fullname_too_long", "fullname_empty"])
def test_register_invalid_fullname_length(fullname_value, description, base_url=API_URL):
    """
    Тест валидации граничных значений длины полного имени.
    """
    allure.dynamic.title(f"Register: Валидация длины имени ({description})")

    timestamp = int(time.time())
    user_email = f"name_limit_{timestamp}@gmail.com"
    user_password = "validPass123"

    with allure.step(f"Подготовка данных с именем длины {len(fullname_value)}"):
        endpoint_data = register_endpoint(
            email=user_email,
            password=user_password,
            full_name=fullname_value,
            terms_accepted=True
        )

    with allure.step("Отправка запроса на регистрацию"):
        url = f"{base_url.rstrip('/')}{endpoint_data['path']}"
        resp = requests.post(url, json=endpoint_data['json'], headers=endpoint_data['headers'])

    with allure.step("Проверка отказа (400 Bad Request)"):
        assert resp.status_code == 400, \
            f"Ожидался статус 400, но получен {resp.status_code}. Длина имени: {len(fullname_value)}"

    with allure.step("Проверка, что ошибка относится к fullName"):
        resp_json = resp.json()
        # Ищем 'fullName' или 'full_name' в тексте ошибки
        assert "fullname" in str(resp_json).lower(), "В ошибке не упоминается поле fullName"