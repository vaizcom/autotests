import time
import allure
import pytest
import requests

from config.settings import API_URL
from test_backend.data.endpoints.User.assert_register_payload import assert_register_payload
from test_backend.data.endpoints.User.register_endpoint import register_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Auth Service")
@allure.suite("Registration")
@pytest.mark.parametrize("email_case_func, title_suffix", [
    (lambda s: s.lower(), "обычный email"),
    (lambda s: s.upper(), "email в верхнем регистре")
], ids=["lowercase", "uppercase"])
def test_register_user_success(email_case_func, title_suffix):
    """
    Параметризованный тест регистрации пользователя (разные регистры email).
    """
    allure.dynamic.title(f"Register: Успешная регистрация ({title_suffix})")

    base_url = API_URL

    # Генерируем уникальный email используя timestamp
    timestamp = int(time.time())
    # Формируем базовый email и применяем функцию изменения регистра
    raw_email = f"autotest_{timestamp}@gmail.com"
    user_email = email_case_func(raw_email)

    user_password = "123456"
    user_name = f"autotest_{timestamp}"

    with allure.step("Подготовка данных для регистрации"):
        endpoint_data = register_endpoint(
            email=user_email,
            password=user_password,
            full_name=user_name,
            terms_accepted=True
        )

    with allure.step(f"Отправка POST запроса на регистрацию: {user_email}"):
        url = f"{base_url.rstrip('/')}{endpoint_data['path']}"

        resp = requests.post(url, json=endpoint_data['json'], headers=endpoint_data['headers'])

    with allure.step("Проверка кода ответа"):
        assert resp.status_code == 200, \
            f"Ожидался статус 200, но получен {resp.status_code}. Ответ: {resp.text}"

    with allure.step("Валидация тела ответа (Полная проверка структуры и типов данных ответа)"):
        resp_json = resp.json()

        # Полная проверка структуры и типов данных ответа
        assert_register_payload(resp_json)

        user_data = resp_json.get('payload')

        # Проверка соответствия отправленных данных
        space_data = user_data.get('space')
        assert space_data is not None, "Объект space отсутствует в ответе"
        assert space_data.get('name') == user_name + "'s Space", "Имя пользователя в ответе не совпадает"

    with allure.step("Проверка безопасности (отсутствие пароля в ответе)"):
        assert 'password' not in user_data, "Критично: Пароль вернулся в ответе сервера!"

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