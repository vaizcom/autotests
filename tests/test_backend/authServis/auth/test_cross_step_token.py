import time

import allure
import pytest
import requests

from config.settings import API_URL
from test_backend.data.endpoints.Auth.auth_with_email_endpoint import auth_with_email_endpoint
from test_backend.data.endpoints.Auth.verify_otp_endpoint import verify_otp_endpoint
from test_backend.data.endpoints.Auth.verify_password_endpoint import verify_password_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Auth")
@allure.sub_suite("Межшаговая подмена tempToken")
def test_password_token_in_verify_otp():
    """
    Негативный тест: tempToken от needPassword (логин) нельзя использовать в VerifyOtp.
    """
    allure.dynamic.title("Межшаговая подмена: password-токен → VerifyOtp")

    base_url = API_URL

    with allure.step("AuthWithEmail — получение tempToken (needPassword)"):
        endpoint = auth_with_email_endpoint(email="mastretsovaone+main@gmail.com")
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])
        assert resp.status_code == 200

        payload = resp.json().get("payload", {})
        assert payload.get("needPassword") is True
        temp_token = payload.get("tempToken")

    with allure.step("VerifyOtp с password-токеном"):
        endpoint = verify_otp_endpoint(temp_token=temp_token, otp="123456")
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 400, \
            f"Ожидался статус 400, получен {resp.status_code}. Ответ: {resp.text}"

    with allure.step("Проверка структуры ошибки"):
        resp_json = resp.json()

        assert resp_json.get("type") == "VerifyOtp"
        assert resp_json.get("payload") is None

        error = resp_json.get("error", {})
        assert error.get("code") == "InvalidForm"
        assert error.get("originalType") == "VerifyOtp"

        fields = error.get("fields", [])
        otp_errors = [f for f in fields if f.get("name") == "otp"]
        assert len(otp_errors) > 0, f"Не найдена ошибка для поля otp. Ответ: {resp_json}"
        assert "OTPCodeNotValid" in otp_errors[0].get("codes", [])


@allure.parent_suite("Auth Service")
@allure.suite("Auth")
@allure.sub_suite("Межшаговая подмена tempToken")
def test_otp_token_in_verify_password():
    """
    Негативный тест: tempToken от needOTP (регистрация) нельзя использовать в VerifyPassword.
    """
    allure.dynamic.title("Межшаговая подмена: otp-токен → VerifyPassword")

    base_url = API_URL
    timestamp = int(time.time())
    new_email = f"autotest_cross_{timestamp}@gmail.com"

    with allure.step("AuthWithEmail — получение tempToken (needOTP)"):
        endpoint = auth_with_email_endpoint(email=new_email)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])
        assert resp.status_code == 200

        payload = resp.json().get("payload", {})
        assert payload.get("needOTP") is True
        temp_token = payload.get("tempToken")

    with allure.step("VerifyPassword с otp-токеном"):
        endpoint = verify_password_endpoint(temp_token=temp_token, password="123456")
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 400, \
            f"Ожидался статус 400, получен {resp.status_code}. Ответ: {resp.text}"

    with allure.step("Проверка структуры ошибки"):
        resp_json = resp.json()

        assert resp_json.get("type") == "VerifyPassword"
        assert resp_json.get("payload") is None

        error = resp_json.get("error", {})
        assert error.get("code") == "InvalidForm"
        assert error.get("originalType") == "VerifyPassword"

        fields = error.get("fields", [])
        password_errors = [f for f in fields if f.get("name") == "password"]
        assert len(password_errors) > 0, f"Не найдена ошибка для поля password. Ответ: {resp_json}"
        assert "WrongCredentials" in password_errors[0].get("codes", [])
