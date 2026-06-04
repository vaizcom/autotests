import time

import allure
import pytest
import requests

from config.settings import API_URL
from test_backend.data.endpoints.Auth.auth_with_email_endpoint import auth_with_email_endpoint
from test_backend.data.endpoints.Auth.verify_otp_endpoint import verify_otp_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("Registration")
@allure.sub_suite("VerifyOtp — негативные")
@pytest.mark.parametrize("otp, expected_error_code, expected_field_code, description", [
    ("000000", "InvalidForm", "OTPCodeNotValid", "неверный OTP"),
    ("", "InvalidForm", "FieldCantBeBlanc", "пустой OTP"),
], ids=["wrong_otp", "empty_otp"])
def test_verify_otp_invalid_code(otp, expected_error_code, expected_field_code, description):
    """
    Негативный тест: VerifyOtp с неверным/пустым OTP-кодом.
    """
    allure.dynamic.title(f"VerifyOtp: отказ — {description}")

    base_url = API_URL
    timestamp = int(time.time())
    new_email = f"autotest_otp_neg_{timestamp}@gmail.com"

    # --- Шаг 1: получаем tempToken с needOTP ---
    with allure.step("AuthWithEmail — получение tempToken (needOTP)"):
        endpoint = auth_with_email_endpoint(email=new_email)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])
        assert resp.status_code == 200, \
            f"AuthWithEmail вернул {resp.status_code}. Ответ: {resp.text}"

        payload = resp.json().get("payload", {})
        assert payload.get("needOTP") is True, \
            f"Ожидался needOTP=true, получено: {payload}"

        temp_token = payload.get("tempToken")
        assert temp_token, "tempToken отсутствует в ответе AuthWithEmail"

    # --- Шаг 2: VerifyOtp с невалидным OTP ---
    with allure.step(f"VerifyOtp — {description}"):
        endpoint = verify_otp_endpoint(temp_token=temp_token, otp=otp)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 400, \
            f"Ожидался статус 400, получен {resp.status_code}. Ответ: {resp.text}"

    with allure.step("Проверка структуры ошибки"):
        resp_json = resp.json()

        assert resp_json.get("type") == "VerifyOtp", \
            f"Ожидался type='VerifyOtp', получено: {resp_json.get('type')}"
        assert resp_json.get("payload") is None, \
            f"Ожидался payload=null, получено: {resp_json.get('payload')}"

        error = resp_json.get("error", {})
        assert error.get("code") == expected_error_code, \
            f"Ожидался error.code='{expected_error_code}', получено: {error.get('code')}"
        assert error.get("originalType") == "VerifyOtp", \
            f"Ожидался originalType='VerifyOtp', получено: {error.get('originalType')}"

    with allure.step(f"Проверка кода ошибки поля: {expected_field_code}"):
        fields = error.get("fields", [])
        otp_errors = [f for f in fields if f.get("name") == "otp"]

        assert len(otp_errors) > 0, \
            f"Не найдена ошибка для поля otp. Ответ: {resp_json}"
        assert expected_field_code in otp_errors[0].get("codes", []), \
            f"Ожидался код {expected_field_code}, получено: {otp_errors[0].get('codes')}"


@allure.parent_suite("Auth Service")
@allure.suite("Registration")
@allure.sub_suite("VerifyOtp — невалидный tempToken")
@pytest.mark.parametrize("temp_token, expected_error_code, description", [
    ("invalid.token", "JwtIncorrect", "мусорный токен"),
    ("", "InvalidForm", "пустой токен"),
], ids=["garbage_token", "empty_token"])
def test_verify_otp_invalid_token(temp_token, expected_error_code, description):
    """
    Негативный тест: VerifyOtp с невалидным tempToken.
    """
    allure.dynamic.title(f"VerifyOtp: отказ — {description}")

    base_url = API_URL

    with allure.step(f"VerifyOtp с невалидным tempToken ({description})"):
        endpoint = verify_otp_endpoint(temp_token=temp_token, otp="123456")
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 400, \
            f"Ожидался статус 400, получен {resp.status_code}. Ответ: {resp.text}"

    with allure.step("Проверка структуры ошибки"):
        resp_json = resp.json()

        assert resp_json.get("type") == "VerifyOtp", \
            f"Ожидался type='VerifyOtp', получено: {resp_json.get('type')}"
        assert resp_json.get("payload") is None, \
            f"Ожидался payload=null, получено: {resp_json.get('payload')}"

        error = resp_json.get("error", {})
        assert error.get("code") == expected_error_code, \
            f"Ожидался error.code='{expected_error_code}', получено: {error.get('code')}"
        assert error.get("originalType") == "VerifyOtp", \
            f"Ожидался originalType='VerifyOtp', получено: {error.get('originalType')}"
