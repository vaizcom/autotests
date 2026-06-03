import allure
import pytest
import requests

from config.settings import API_URL
from test_backend.data.endpoints.Auth.auth_with_email_endpoint import auth_with_email_endpoint
from test_backend.data.endpoints.Auth.verify_password_endpoint import verify_password_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Login")
@allure.sub_suite("VerifyPassword — негативные")
@pytest.mark.parametrize("wrong_password, expected_code, description", [
    ("wrong_password", "WrongCredentials", "неверный пароль"),
    ("", "FieldCantBeBlanc", "пустой пароль"),
], ids=["wrong_password", "empty_password"])
def test_verify_password_wrong_credentials(wrong_password, expected_code, description):
    """
    Негативный тест: VerifyPassword с неверным/пустым паролем.
    """
    allure.dynamic.title(f"VerifyPassword: отказ — {description}")

    base_url = API_URL
    user_email = "mastretsovaone+main@gmail.com"

    # --- Шаг 1: получаем tempToken ---
    with allure.step("Шаг 1: AuthWithEmail — получение tempToken"):
        endpoint = auth_with_email_endpoint(email=user_email)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])
        assert resp.status_code == 200, \
            f"AuthWithEmail вернул {resp.status_code}. Ответ: {resp.text}"

        payload = resp.json().get("payload", {})
        temp_token = payload.get("tempToken")
        assert temp_token, "tempToken отсутствует в ответе AuthWithEmail"

    # --- Шаг 2: VerifyPassword с неверным паролем ---
    with allure.step(f"Шаг 2: VerifyPassword с неверным паролем ({description})"):
        endpoint = verify_password_endpoint(temp_token=temp_token, password=wrong_password)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 400, \
            f"Ожидался статус 400, получен {resp.status_code}. Ответ: {resp.text}"

    with allure.step("Проверка структуры ошибки"):
        resp_json = resp.json()

        assert resp_json.get("type") == "VerifyPassword", \
            f"Ожидался type='VerifyPassword', получено: {resp_json.get('type')}"
        assert resp_json.get("payload") is None, \
            f"Ожидался payload=null, получено: {resp_json.get('payload')}"

        error = resp_json.get("error", {})
        assert error.get("code") == "InvalidForm", \
            f"Ожидался error.code='InvalidForm', получено: {error.get('code')}"
        assert error.get("originalType") == "VerifyPassword", \
            f"Ожидался originalType='VerifyPassword', получено: {error.get('originalType')}"

    with allure.step(f"Проверка кода ошибки поля: {expected_code}"):
        fields = error.get("fields", [])
        password_errors = [f for f in fields if f.get("name") == "password"]

        assert len(password_errors) > 0, \
            f"Не найдена ошибка для поля password. Ответ: {resp_json}"
        assert expected_code in password_errors[0].get("codes", []), \
            f"Ожидался код {expected_code}, получено: {password_errors[0].get('codes')}"
