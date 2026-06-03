import allure
import pytest
import requests

from config.settings import API_URL
from test_backend.data.endpoints.Auth.auth_with_email_endpoint import auth_with_email_endpoint
from test_backend.data.endpoints.Auth.verify_password_endpoint import verify_password_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Login")
@allure.sub_suite("VerifyPassword — невалидный tempToken")
@pytest.mark.parametrize("temp_token, expected_error_code, description", [
    ("invalid.token.value", "JwtIncorrect", "мусорный токен"),
    ("", "InvalidForm", "пустой токен"),
], ids=["garbage_token", "empty_token"])
def test_verify_password_invalid_temp_token(temp_token, expected_error_code, description):
    """
    Негативный тест: VerifyPassword без прохождения AuthWithEmail.
    """
    allure.dynamic.title(f"VerifyPassword: отказ — {description}")

    base_url = API_URL

    with allure.step(f"VerifyPassword с невалидным tempToken ({description})"):
        endpoint = verify_password_endpoint(temp_token=temp_token, password="123456")
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
        assert error.get("code") == expected_error_code, \
            f"Ожидался error.code='{expected_error_code}', получено: {error.get('code')}"
        assert error.get("originalType") == "VerifyPassword", \
            f"Ожидался originalType='VerifyPassword', получено: {error.get('originalType')}"


@allure.parent_suite("Auth Service")
@allure.suite("Login")
@allure.sub_suite("VerifyPassword — невалидный tempToken")
def test_verify_auth_token_as_temp_token():
    """
    Негативный тест: authToken от успешного логина не подходит как tempToken.
    """
    allure.dynamic.title("VerifyPassword: отказ — authToken вместо tempToken")

    base_url = API_URL
    user_email = "mastretsovaone+main@gmail.com"
    user_password = "123456"

    # --- Полный логин для получения authToken ---
    with allure.step("Полный логин: AuthWithEmail → VerifyPassword"):
        endpoint = auth_with_email_endpoint(email=user_email)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"
        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])
        temp_token = resp.json().get("payload", {}).get("tempToken")

        endpoint = verify_password_endpoint(temp_token=temp_token, password=user_password)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"
        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])
        auth_token = resp.json().get("payload", {}).get("authToken")
        assert auth_token, "Не удалось получить authToken для теста"

    # --- Попытка использовать authToken как tempToken ---
    with allure.step("VerifyPassword с authToken вместо tempToken"):
        endpoint = verify_password_endpoint(temp_token=auth_token, password=user_password)
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
        assert error.get("code") == "JwtDoesNotExits", \
            f"Ожидался error.code='JwtDoesNotExits', получено: {error.get('code')}"
        assert error.get("originalType") == "VerifyPassword", \
            f"Ожидался originalType='VerifyPassword', получено: {error.get('originalType')}"
