import time
import allure
import requests
import pytest

from config.settings import API_URL
from test_backend.data.endpoints.User.register_endpoint import register_endpoint

pytestmark = [pytest.mark.backend]

MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 64


@allure.parent_suite("Auth Service")
@allure.suite("Registration Validation")
@pytest.mark.parametrize("valid_password", [
    ("      1"),  # Только пробелы Заведен Баг APP-4479
    ("  123456  "),  # Пробелы по краям
    ("!@#$%^&*()"),  # Спецсимволы
    ("пароль123"),  # Кириллица
    ("Pass🔑word"),  # Emoji (проверка поддержки Unicode/UTF-8)
], ids=["only_spaces", "spaces_trim", "special_chars", "cyrillic", "emoji"])
def test_register_valid_complex_passwords(valid_password, base_url=API_URL):
    """
    Тест регистрации и входа с нестандартными паролями (спецсимволы, юникод, пробелы).
    Проверяет отсутствие проблем с кодировкой и скрытого изменения пароля (trimming).
    """
    allure.dynamic.title(f"Register & Login: Пароль {valid_password}")

    timestamp = int(time.time())
    # Используем hex, чтобы избежать проблем с url-кодированием в email, если вдруг они есть
    user_email = f"complex_pass_{timestamp}_{hash(valid_password)}@gmail.com"
    user_name = f"user_{timestamp}"

    # --- Шаг 1: Регистрация ---
    with allure.step(f"Регистрация пользователя с паролем: '{valid_password}'"):
        endpoint_data = register_endpoint(
            email=user_email,
            password=valid_password,
            full_name=user_name,
            terms_accepted=True
        )

        url_register = f"{base_url.rstrip('/')}{endpoint_data['path']}"
        resp_reg = requests.post(
            url_register,
            json=endpoint_data['json'],
            headers=endpoint_data['headers']
        )

        assert resp_reg.status_code == 200, \
            f"Регистрация не удалась. Статус: {resp_reg.status_code}. Ответ: {resp_reg.text}"

    # --- Шаг 2: Вход в систему (Login) ---
    with allure.step("Попытка входа (Login) с тем же паролем"):
        login_url = f"{base_url.rstrip('/')}/login"
        login_payload = {
            "email": user_email,
            "password": valid_password
        }

        resp_login = requests.post(
            login_url,
            json=login_payload,
            headers={"Content-Type": "application/json"}
        )

        assert resp_login.status_code == 202, \
            f"Не удалось войти с созданным паролем. Возможна проблема кодировки или trimming. " \
            f"Статус: {resp_login.status_code}. Ответ: {resp_login.text}"

        # Дополнительная проверка на наличие токена
        token = resp_login.json().get('payload', {}).get('token')
        assert token is not None, "Токен авторизации не получен после входа"


@allure.parent_suite("Auth Service")
@allure.suite("Registration Validation")
@pytest.mark.parametrize("password_value, description", [
    ("", "Пустой пароль"),
    ("a" * (MIN_PASSWORD_LENGTH - 1), f"Пароль короче минимума ({MIN_PASSWORD_LENGTH - 1} симв.)"),
    ("a" * (MAX_PASSWORD_LENGTH + 1), f"Пароль длиннее максимума ({MAX_PASSWORD_LENGTH + 1} симв.)")
], ids=["password_empty", "password_too_short", "password_too_long"])
def test_register_invalid_password_length(password_value, description, base_url=API_URL):
    """
    Тест валидации граничных значений длины пароля.
    """
    allure.dynamic.title(f"Register: Валидация длины пароля ({description})")

    timestamp = int(time.time())
    user_email = f"pass_limit_{timestamp}@gmail.com"
    user_name = f"user_{timestamp}"

    with allure.step(f"Подготовка данных с паролем длины {len(password_value)}"):
        endpoint_data = register_endpoint(
            email=user_email,
            password=password_value,
            full_name=user_name,
            terms_accepted=True
        )

    with allure.step("Отправка запроса на регистрацию"):
        url = f"{base_url.rstrip('/')}{endpoint_data['path']}"
        resp = requests.post(url, json=endpoint_data['json'], headers=endpoint_data['headers'])

    with allure.step("Проверка отказа (400 Bad Request)"):
        assert resp.status_code == 400, \
            f"Ожидался статус 400, но получен {resp.status_code}. Длина пароля: {len(password_value)}"

    with allure.step("Проверка, что ошибка относится к password"):
        resp_json = resp.json()
        assert "password" in str(resp_json).lower(), "В ошибке не упоминается поле password"