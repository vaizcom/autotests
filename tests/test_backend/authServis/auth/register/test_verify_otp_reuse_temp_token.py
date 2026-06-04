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
    payload_json = base64.urlsafe_b64decode(payload_part + '==')
    token_data = json.loads(payload_json)
    confirm_id = token_data['id']

    doc = db.confirmtokens.find_one({'_id': ObjectId(confirm_id)})
    assert doc, f"Запись confirmtokens с _id={confirm_id} не найдена"

    otp_code = doc.get('payload', {}).get('otpCode')
    assert otp_code, f"otpCode отсутствует в confirmtokens. Документ: {doc}"

    return otp_code


@allure.parent_suite("Auth Service")
@allure.suite("New_Registration")
@allure.sub_suite("VerifyOtp — повторное использование tempToken")
def test_verify_otp_reuse_temp_token(db):
    """
    Негативный тест: tempToken нельзя использовать повторно после успешной регистрации.
    """
    allure.dynamic.title("VerifyOtp: отказ — повторное использование tempToken")

    base_url = API_URL
    timestamp = int(time.time())
    new_email = f"autotest_reuse_{timestamp}@gmail.com"

    # --- Шаг 1: получаем tempToken ---
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

    # --- Шаг 2: достаём OTP из MongoDB ---
    with allure.step("Получение OTP-кода из MongoDB"):
        otp_code = get_otp_from_mongo(db, temp_token)

    # --- Шаг 3: успешная регистрация ---
    with allure.step("VerifyOtp — успешная регистрация"):
        endpoint = verify_otp_endpoint(temp_token=temp_token, otp=otp_code)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])
        assert resp.status_code == 200, \
            f"VerifyOtp вернул {resp.status_code}. Ответ: {resp.text}"

        auth_token = resp.json().get("payload", {}).get("authToken")
        assert auth_token, "authToken отсутствует в ответе VerifyOtp"

    # --- Шаг 4: повторное использование того же tempToken ---
    with allure.step("Повторный VerifyOtp с тем же tempToken"):
        endpoint = verify_otp_endpoint(temp_token=temp_token, otp=otp_code)
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
        assert error.get("code") == "JwtDoesNotExits", \
            f"Ожидался error.code='JwtDoesNotExits', получено: {error.get('code')}"
        assert error.get("originalType") == "VerifyOtp", \
            f"Ожидался originalType='VerifyOtp', получено: {error.get('originalType')}"
