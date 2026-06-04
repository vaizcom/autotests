import time
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
    """
    Декодирует tempToken JWT, достаёт id и находит OTP в confirmtokens.

    В браузере https://www.jwt.io/ вставить tempToken и получить id,
    Этот id = _id записи в коллекции confirmtokens,
    найти в монго по запросу {_id:ObjectId('id')} и извлеч otp_code
    """

    payload_part = temp_token.split('.')[1]
    # Добавляем padding для base64
    payload_json = base64.urlsafe_b64decode(payload_part + '==')
    token_data = json.loads(payload_json)
    confirm_id = token_data['id']

    doc = db.confirmtokens.find_one({'_id': ObjectId(confirm_id)})
    assert doc, f"Запись confirmtokens с _id={confirm_id} не найдена"

    otp_code = doc.get('payload', {}).get('otpCode')
    assert otp_code, f"otpCode отсутствует в confirmtokens. Документ: {doc}"

    return otp_code


@allure.parent_suite("Auth Service")
@allure.suite("Registration")
@allure.sub_suite("AuthWithEmail + VerifyOtp")
def test_register_via_auth_with_email(db):
    """
    Новый флоу регистрации: AuthWithEmail → OTP из Mongo → VerifyOtp.
    """
    allure.dynamic.title("Register (AuthWithEmail): Успешная регистрация нового пользователя")

    base_url = API_URL
    timestamp = int(time.time())
    new_email = f"autotest_{timestamp}@gmail.com"

    # --- Шаг 1: AuthWithEmail с новым email ---
    with allure.step(f"Шаг 1: AuthWithEmail — новый email {new_email}"):
        endpoint = auth_with_email_endpoint(email=new_email)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 200, \
            f"AuthWithEmail вернул {resp.status_code}. Ответ: {resp.text}"

        resp_json = resp.json()
        assert resp_json.get("type") == "AuthWithEmail", \
            f"Ожидался type='AuthWithEmail', получено: {resp_json.get('type')}"

        payload = resp_json.get("payload", {})
        assert payload.get("needOTP") is True, \
            f"Ожидался needOTP=true для нового email, получено: {payload}"

        temp_token = payload.get("tempToken")
        assert temp_token, "tempToken отсутствует в ответе AuthWithEmail"

    # --- Шаг 2: достаём OTP из MongoDB ---
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
        payload = resp_json.get("payload", {})

        auth_token = payload.get("authToken")
        assert auth_token, "authToken отсутствует в ответе VerifyOtp"

        assert payload.get("newUser") is True, \
            f"Ожидался newUser=true для нового пользователя, получено: {payload.get('newUser')}"
