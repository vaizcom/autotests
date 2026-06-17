import base64
import json

import allure
import pytest
import requests
from bson import ObjectId

from config.settings import API_URL
from test_backend.data.endpoints.Auth.auth_with_email_endpoint import auth_with_email_endpoint
from test_backend.data.endpoints.Auth.verify_otp_endpoint import verify_otp_endpoint

pytestmark = [pytest.mark.backend]

_EMAIL = "tst_signin_otp@mailinator.com"
_WRONG_OTP = "000000"
_MAX_ATTEMPTS = 5


def get_otp_from_mongo(db, temp_token):
    """Декодирует tempToken JWT, достаёт id и находит OTP в confirmtokens."""
    payload_part = temp_token.split('.')[1]
    payload_json = base64.urlsafe_b64decode(payload_part + '==')
    token_data = json.loads(payload_json)
    confirm_id = token_data['id']

    doc = db.confirmtokens.find_one({'_id': ObjectId(confirm_id)})
    assert doc, f"Запись confirmtokens с _id={confirm_id} не найдена"

    otp_code = doc.get('payload', {}).get('otpCode')
    assert otp_code, f"otpCode отсутствует в confirmtokens. Документ: {doc}"

    return otp_code


@allure.parent_suite("Auth Service")
@allure.suite("New_Login")
@allure.sub_suite("VerifyOtp — защита от перебора")
def test_otp_max_attempts(db):
    """
    Защита от brute-force: после 5 неверных OTP токен инвалидируется.
    Попытки 1-4 → OTPCodeNotValid, 5-я → OTPMaxAttemptsReached,
    6-я (валидный OTP) → JwtDoesNotExits.
    """
    allure.dynamic.title("VerifyOtp: блокировка после 5 неверных попыток")

    base_url = API_URL

    # --- Шаг 1: AuthWithEmail ---
    with allure.step(f"AuthWithEmail — получение tempToken ({_EMAIL})"):
        endpoint = auth_with_email_endpoint(email=_EMAIL)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])
        assert resp.status_code == 200, \
            f"AuthWithEmail вернул {resp.status_code}. Ответ: {resp.text}"

        payload = resp.json().get("payload", {})
        assert payload.get("needOTP") is True
        temp_token = payload.get("tempToken")
        assert temp_token, "tempToken отсутствует в ответе AuthWithEmail"

    # --- Получаем валидный OTP из MongoDB ---
    with allure.step("Получение валидного OTP из MongoDB"):
        valid_otp = get_otp_from_mongo(db, temp_token)

    # --- Шаг 2: попытки 1–4 → OTPCodeNotValid ---
    for i in range(1, _MAX_ATTEMPTS):
        with allure.step(f"Попытка {i}/{_MAX_ATTEMPTS}: неверный OTP → OTPCodeNotValid"):
            endpoint = verify_otp_endpoint(temp_token=temp_token, otp=_WRONG_OTP)
            url = f"{base_url.rstrip('/')}{endpoint['path']}"

            resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

            assert resp.status_code == 400, \
                f"Попытка {i}: ожидался статус 400, получен {resp.status_code}"

            resp_json = resp.json()
            error = resp_json.get("error", {})
            assert error.get("code") == "InvalidForm", \
                f"Попытка {i}: ожидался error.code='InvalidForm', получено: {error.get('code')}"

            fields = error.get("fields", [])
            otp_errors = [f for f in fields if f.get("name") == "otp"]
            assert otp_errors and "OTPCodeNotValid" in otp_errors[0].get("codes", []), \
                f"Попытка {i}: ожидался OTPCodeNotValid. Ответ: {resp_json}"

    # --- Шаг 3: попытка 5 → OTPMaxAttemptsReached ---
    with allure.step(f"Попытка {_MAX_ATTEMPTS}/{_MAX_ATTEMPTS}: лимит исчерпан → OTPMaxAttemptsReached"):
        endpoint = verify_otp_endpoint(temp_token=temp_token, otp=_WRONG_OTP)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 400, \
            f"Попытка {_MAX_ATTEMPTS}: ожидался статус 400, получен {resp.status_code}"

        resp_json = resp.json()
        error = resp_json.get("error", {})
        assert error.get("code") == "OTPMaxAttemptsReached", \
            f"Ожидался error.code='OTPMaxAttemptsReached', получено: {error.get('code')}"

    # --- Шаг 4: попытка 6 с валидным OTP → токен недействителен ---
    with allure.step(f"Попытка после лимита: валидный OTP ({valid_otp}) → JwtDoesNotExits"):
        endpoint = verify_otp_endpoint(temp_token=temp_token, otp=valid_otp)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 400, \
            f"Ожидался статус 400, получен {resp.status_code}"

        resp_json = resp.json()
        error = resp_json.get("error", {})
        assert error.get("code") == "JwtDoesNotExits", \
            f"Ожидался error.code='JwtDoesNotExits', получено: {error.get('code')}"
