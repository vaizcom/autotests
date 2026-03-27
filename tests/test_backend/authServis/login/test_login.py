import allure
import pytest
import requests

from config.settings import API_URL

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Auth Service")
@allure.suite("Login")
@pytest.mark.parametrize("email_case_func, title_suffix", [
    (lambda s: s.lower(), "обычный email"),
    (lambda s: s.upper(), "email в верхнем регистре")
], ids=["lowercase", "uppercase"])
def test_login_user_success(email_case_func, title_suffix):
    """
    Параметризованный тест login пользователя (разные регистры email).
    """
    allure.dynamic.title(f"Login: Успешный Login ({title_suffix})")

    base_url = API_URL

    # Формируем базовый email и применяем функцию изменения регистра
    raw_email = "mastretsovaone+main@gmail.com"
    user_email = email_case_func(raw_email)

    user_password = "123456"

    with allure.step("Проверка успешного входа (Login) с зарегистрированными данными"):
        login_payload = {
            "email": user_email,
            "password": user_password
        }
        login_url = f"{base_url.rstrip('/')}/login"

        resp_login = requests.post(
            login_url,
            json=login_payload,
            headers={"Content-Type": "application/json"}
        )

        assert resp_login.status_code == 202, \
            f"Не удалось войти в систему. Статус: {resp_login.status_code}. Ответ: {resp_login.text}"

        # Дополнительно проверяем, что токен действительно пришел
        login_resp_json = resp_login.json()
        token = login_resp_json.get('payload', {}).get('token')
        assert token is not None, "В ответе логина не найден токен авторизации!"