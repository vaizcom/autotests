import allure
import pytest
import requests

from config.settings import API_URL
from test_backend.data.endpoints.Auth.auth_with_email_endpoint import auth_with_email_endpoint
from test_backend.data.endpoints.Auth.verify_password_endpoint import verify_password_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("New_Login")
@allure.sub_suite("AuthWithEmail + VerifyPassword")
@pytest.mark.parametrize("email_case_func, title_suffix", [
    (lambda s: s.lower(), "обычный email"),
    (lambda s: s.upper(), "email в верхнем регистре")
], ids=["lowercase", "uppercase"])
def test_login_via_auth_with_email(email_case_func, title_suffix):
    """
    Новый флоу логина: AuthWithEmail → VerifyPassword.
    Проверяет двухшаговую авторизацию для существующего пользователя.
    """
    allure.dynamic.title(f"Login (AuthWithEmail): Успешный логин ({title_suffix})")

    base_url = API_URL
    raw_email = "mastretsovaone+main@gmail.com"
    user_email = email_case_func(raw_email)
    user_password = "123456"

    # --- Шаг 1: AuthWithEmail ---
    with allure.step("Шаг 1: AuthWithEmail — определение типа авторизации"):
        endpoint = auth_with_email_endpoint(email=user_email)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 200, \
            f"AuthWithEmail вернул {resp.status_code}. Ответ: {resp.text}"

        resp_json = resp.json()
        assert resp_json.get("type") == "AuthWithEmail", \
            f"Ожидался type='AuthWithEmail', получено: {resp_json.get('type')}"

        payload = resp_json.get("payload", {})
        assert payload.get("needPassword") is True, \
            f"Ожидался needPassword=true для существующего email, получено: {payload}"

        temp_token = payload.get("tempToken")
        assert temp_token, "tempToken отсутствует в ответе AuthWithEmail"

    # --- Шаг 2: VerifyPassword ---
    with allure.step("Шаг 2: VerifyPassword — подтверждение пароля"):
        endpoint = verify_password_endpoint(temp_token=temp_token, password=user_password)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 200, \
            f"VerifyPassword вернул {resp.status_code}. Ответ: {resp.text}"

        resp_json = resp.json()
        payload = resp_json.get("payload", {})

        auth_token = payload.get("authToken")
        assert auth_token, "authToken отсутствует в ответе VerifyPassword"

        assert payload.get("newUser") is False, \
            f"Ожидался newUser=false для существующего пользователя, получено: {payload.get('newUser')}"
