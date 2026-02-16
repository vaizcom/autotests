import time
import allure
import requests
import pytest

from config.settings import API_URL
from test_backend.data.endpoints.User.register_endpoint import register_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Registration Validation")
@pytest.mark.parametrize("terms_value, expected_status, description", [
    (True, 200, "Позитивный: Условия приняты"),
    (False, 400, "Негативный: Условия отклонены")
], ids=["terms_true", "terms_false"])
def test_register_terms_validation(terms_value, expected_status, description, base_url=API_URL):
    """
    Параметризованный тест: проверяет регистрацию при termsAccepted = True и False.
    В случае ошибки (False) проверяет структуру JSON ошибки.
    """
    allure.dynamic.title(f"Register: termsAccepted={terms_value} -> Ожидаем {expected_status}")

    timestamp = int(time.time())
    user_email = f"terms_{str(terms_value).lower()}_{timestamp}@gmail.com"
    user_password = "validPass123"
    user_name = f"User Terms {terms_value}"

    with allure.step(f"Подготовка данных: termsAccepted={terms_value}"):
        endpoint_data = register_endpoint(
            email=user_email,
            password=user_password,
            full_name=user_name,
            terms_accepted=terms_value
        )

    with allure.step("Отправка запроса"):
        url = f"{base_url.rstrip('/')}{endpoint_data['path']}"
        resp = requests.post(url, json=endpoint_data['json'], headers=endpoint_data['headers'])

    with allure.step(f"Проверка статус-кода (Ожидаем {expected_status})"):
        assert resp.status_code == expected_status, \
            f"Неверный статус! Ожидалось: {expected_status}, Получено: {resp.status_code}. Тело: {resp.text}"

    # Если ожидаем ошибку (400), проверяем детали ошибки в JSON
    if expected_status == 400:
        with allure.step("Валидация тела ошибки (InvalidForm / TermsNotAccepted)"):
            resp_json = resp.json()
            error_data = resp_json.get("error", {})

            # 1. Проверяем общий код ошибки
            assert error_data.get("code") == "InvalidForm", \
                f"Ожидался код ошибки InvalidForm, получен: {error_data.get('code')}"

            # 2. Ищем поле termsAccepted в списке fields
            fields = error_data.get("fields", [])
            terms_error = next((f for f in fields if f.get("name") == "termsAccepted"), None)

            assert terms_error is not None, \
                f"В списке ошибок не найдено поле 'termsAccepted'. Список полей: {fields}"

            # 3. Проверяем конкретный код ошибки поля
            assert "TermsNotAccepted" in terms_error.get("codes", []), \
                f"Ожидался код ошибки поля TermsNotAccepted. Получено: {terms_error.get('codes')}"