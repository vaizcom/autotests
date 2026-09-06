import base64
import json as _json
import time

import pytest
import requests
from bson import ObjectId

from config.settings import API_URL
from core.client import APIClient
from test_backend.data.endpoints.Auth.auth_with_email_endpoint import auth_with_email_endpoint
from test_backend.data.endpoints.Auth.verify_otp_endpoint import verify_otp_endpoint
from test_backend.data.endpoints.Space.space_endpoints import get_spaces_endpoint


def short_resp(resp, max_len=300):
    return resp.text[:max_len]


@pytest.fixture(scope="session")
def temp_client(db):
    """
    Регистрирует нового пользователя через AuthWithEmail → VerifyOtp,
    возвращает готовый APIClient и ID спейса для тестов.
    """
    base_url = API_URL
    timestamp = int(time.time())
    email = f"space_{timestamp}@autotest.com"

    # 1. AuthWithEmail — получаем tempToken
    ep = auth_with_email_endpoint(email=email)
    resp = requests.post(f"{base_url.rstrip('/')}{ep['path']}", json=ep['json'], headers=ep['headers'], timeout=10)
    assert resp.status_code == 200, f"AuthWithEmail вернул {resp.status_code}: {short_resp(resp)}"

    payload = resp.json().get("payload", {})
    assert payload.get("needOTP") is True, f"Ожидался needOTP=true, получено: {payload}"
    temp_token = payload["tempToken"]

    # 2. Получаем OTP из MongoDB
    token_payload = _json.loads(base64.urlsafe_b64decode(temp_token.split('.')[1] + '=='))
    doc = db.confirmtokens.find_one({'_id': ObjectId(token_payload['id'])})
    assert doc, f"Запись confirmtokens с _id={token_payload['id']} не найдена"
    otp_code = doc.get('payload', {}).get('otpCode')
    assert otp_code, "otpCode отсутствует в confirmtokens"

    # 3. VerifyOtp — получаем authToken
    ep = verify_otp_endpoint(temp_token=temp_token, otp=otp_code)
    resp = requests.post(f"{base_url.rstrip('/')}{ep['path']}", json=ep['json'], headers=ep['headers'], timeout=10)
    assert resp.status_code == 200, f"VerifyOtp вернул {resp.status_code}: {short_resp(resp)}"

    auth_token = resp.json().get("payload", {}).get("authToken")
    assert auth_token, "authToken отсутствует в ответе VerifyOtp"

    # 4. Получаем space_id из GetSpaces
    client = APIClient(base_url=base_url, token=auth_token)
    spaces_resp = client.post(**get_spaces_endpoint())
    assert spaces_resp.status_code == 200, f"GetSpaces вернул {spaces_resp.status_code}: {short_resp(spaces_resp)}"
    spaces = spaces_resp.json().get("payload", {}).get("spaces", [])
    assert spaces, "У нового пользователя нет спейсов"
    space_id = spaces[0]["_id"]

    return client, space_id
