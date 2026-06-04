import allure
import pytest
import requests

from config.settings import API_URL
from test_backend.data.endpoints.Auth.auth_with_email_endpoint import auth_with_email_endpoint
from test_backend.data.endpoints.Auth.verify_password_endpoint import verify_password_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("New_Login")
@allure.sub_suite("VerifyPassword — повторное использование tempToken")
def test_verify_reuse_temp_token():
    """
    Негативный тест: tempToken нельзя использовать повторно после успешного логина.
    """
    allure.dynamic.title("VerifyPassword: отказ — повторное использование tempToken")

    base_url = API_URL
    user_email = "mastretsovaone+main@gmail.com"
    user_password = "123456"

    # --- Шаг 1: получаем tempToken ---
    with allure.step("AuthWithEmail — получение tempToken"):
        endpoint = auth_with_email_endpoint(email=user_email)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])
        assert resp.status_code == 200, \
            f"AuthWithEmail вернул {resp.status_code}. Ответ: {resp.text}"

        temp_token = resp.json().get("payload", {}).get("tempToken")
        assert temp_token, "tempToken отсутствует в ответе AuthWithEmail"

    # --- Шаг 2: успешный логин ---
    with allure.step("VerifyPassword — успешный логин"):
        endpoint = verify_password_endpoint(temp_token=temp_token, password=user_password)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])
        assert resp.status_code == 200, \
            f"VerifyPassword вернул {resp.status_code}. Ответ: {resp.text}"

        auth_token = resp.json().get("payload", {}).get("authToken")
        assert auth_token, "authToken отсутствует в ответе VerifyPassword"

    # --- Шаг 3: повторное использование того же tempToken ---
    with allure.step("Повторный VerifyPassword с тем же tempToken"):
        endpoint = verify_password_endpoint(temp_token=temp_token, password=user_password)
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
