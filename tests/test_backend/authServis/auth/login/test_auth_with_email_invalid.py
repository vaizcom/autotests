import allure
import pytest
import requests

from config.settings import API_URL
from test_backend.data.endpoints.Auth.auth_with_email_endpoint import auth_with_email_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Auth Service")
@allure.suite("New_Login")
@allure.sub_suite("AuthWithEmail — невалидный email")
@pytest.mark.parametrize("invalid_email, description", [
    ("invalid-email-format", "без @"),
    ("user@domain", "без зоны домена"),
    ("user name@domain.com", "пробелы в адресе"),
    ("", "пустой email"),
], ids=["no_at", "no_domain_zone", "spaces", "empty"])
def test_auth_with_email_invalid(invalid_email, description):
    """
    Негативный тест: AuthWithEmail с некорректным email.
    """
    allure.dynamic.title(f"AuthWithEmail: отказ — {description}")

    base_url = API_URL

    with allure.step(f"Отправка AuthWithEmail с невалидным email: '{invalid_email}'"):
        endpoint = auth_with_email_endpoint(email=invalid_email)
        url = f"{base_url.rstrip('/')}{endpoint['path']}"

        resp = requests.post(url, json=endpoint['json'], headers=endpoint['headers'])

        assert resp.status_code == 400, \
            f"Ожидался статус 400, получен {resp.status_code}. Ответ: {resp.text}"

    with allure.step("Проверка структуры ошибки"):
        resp_json = resp.json()

        assert resp_json.get("type") == "AuthWithEmail", \
            f"Ожидался type='AuthWithEmail', получено: {resp_json.get('type')}"
        assert resp_json.get("payload") is None, \
            f"Ожидался payload=null, получено: {resp_json.get('payload')}"

        error = resp_json.get("error", {})
        assert error.get("code") == "InvalidForm", \
            f"Ожидался error.code='InvalidForm', получено: {error.get('code')}"
        assert error.get("originalType") == "AuthWithEmail", \
            f"Ожидался originalType='AuthWithEmail', получено: {error.get('originalType')}"

    with allure.step("Проверка кода ошибки поля: InvalidEmail"):
        fields = error.get("fields", [])
        email_errors = [f for f in fields if f.get("name") == "email"]

        assert len(email_errors) > 0, \
            f"Не найдена ошибка для поля email. Ответ: {resp_json}"
        assert "InvalidEmail" in email_errors[0].get("codes", []), \
            f"Ожидался код InvalidEmail, получено: {email_errors[0].get('codes')}"
