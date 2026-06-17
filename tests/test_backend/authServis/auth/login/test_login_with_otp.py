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
@allure.sub_suite("AuthWithEmail + VerifyOtp")
@pytest.mark.parametrize("email_case_func, title_suffix", [
    (lambda s: s.lower(), "обычный email"),
    (lambda s: s.upper(), "email в верхнем регистре")
], ids=["lowercase", "uppercase"])
def test_login_with_otp(db, email_case_func, title_suffix):
    """
    Флоу логина через OTP: AuthWithEmail → OTP из Mongo → VerifyOtp.
    Проверяет двухшаговую авторизацию для существующего пользователя без пароля.
    """
    allure.dynamic.title(f"Login (OTP): Успешный логин ({title_suffix})")

    base_url = API_URL
    raw_email = "tst_signin_otp@mailinator.com"
    user_email = email_case_func(raw_email)

    # --- Шаг 1: AuthWithEmail ---
    with allure.step(f"Шаг 1: AuthWithEmail — определение типа авторизации ({user_email})"):
        endpoint = auth_with_email_endpoint(email=user_email)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 200, \
            f"AuthWithEmail вернул {resp.status_code}. Ответ: {resp.text}"

        resp_json = resp.json()
        assert resp_json.get("type") == "AuthWithEmail", \
            f"Ожидался type='AuthWithEmail', получено: {resp_json.get('type')}"

        payload = resp_json.get("payload", {})
        assert payload.get("needOTP") is True, \
            f"Ожидался needOTP=true для пользователя без пароля, получено: {payload}"

        temp_token = payload.get("tempToken")
        assert temp_token, "tempToken отсутствует в ответе AuthWithEmail"

    # --- Шаг 2: OTP из MongoDB ---
    with allure.step("Шаг 2: Получение OTP-кода из MongoDB"):
        otp_code = get_otp_from_mongo(db, temp_token)

    # --- Шаг 3: VerifyOtp ---
    with allure.step(f"Шаг 3: VerifyOtp — подтверждение OTP ({otp_code})"):
        endpoint = verify_otp_endpoint(temp_token=temp_token, otp=otp_code)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 200, \
            f"VerifyOtp вернул {resp.status_code}. Ответ: {resp.text}"

        resp_json = resp.json()
        assert resp_json.get("type") == "VerifyOtp", \
            f"Ожидался type='VerifyOtp', получено: {resp_json.get('type')}"

        payload = resp_json.get("payload", {})

        auth_token = payload.get("authToken")
        assert auth_token, "authToken отсутствует в ответе VerifyOtp"

        assert payload.get("newUser") is False, \
            f"Ожидался newUser=false для существующего пользователя, получено: {payload.get('newUser')}"
