import time
import allure
import requests
import pytest

from config.settings import API_URL
from test_backend.data.endpoints.User.assert_register_payload import assert_register_payload
from test_backend.data.endpoints.User.register_endpoint import register_endpoint

pytestmark = [pytest.mark.backend]

MAX_FULL_NAME_LENGTH = 30


@allure.parent_suite("Auth Service")
@allure.suite("Registration Validation")
@allure.sub_suite("Fullname Validation")
@pytest.mark.parametrize("valid_fullname, description", [
    ("A" * MAX_FULL_NAME_LENGTH, "Максимальная длина"),
    ("O'Connor-Björn 陈 Иван", "Смешанные символы (Unicode)"), # Проверяет сразу: Кириллицу, Китайский, Дефис, Апостроф, Умляуты
    ("  User Name", "Пробелы в начале и конце") # Пробелы по краям (Проверка Trim) Трим только вначале
], ids=["max_len", "complex_unicode", "trim_spaces"])
def test_register_valid_fullname(valid_fullname, description, base_url=API_URL):
    """
    Позитивный тест регистрации с различными вариантами полного имени.
    """
    allure.dynamic.title(f"Register: Успешная регистрация с именем '{valid_fullname}'")

    timestamp = int(time.time())
    # Используем hash, чтобы email был уникальным даже для одинаковых имен
    user_email = f"name_{timestamp}_{abs(hash(valid_fullname))}@gmail.com"
    user_password = "validPass123"

    with allure.step(f"Подготовка данных: {valid_fullname}"):
        endpoint_data = register_endpoint(
            email=user_email,
            password=user_password,
            full_name=valid_fullname,
            terms_accepted=True
        )

    with allure.step("Отправка запроса"):
        url = f"{base_url.rstrip('/')}{endpoint_data['path']}"
        resp = requests.post(url, json=endpoint_data['json'], headers=endpoint_data['headers'])

    with allure.step("Проверка успеха (200 OK)"):
        assert resp.status_code == 200, \
            f"Ошибка регистрации. Статус: {resp.status_code}. Ответ: {resp.text}"

    with allure.step("Валидация сохранения имени"):
        user_data = resp.json().get('payload').get('space')
        saved_name = user_data.get('name')

    with allure.step("Валидация тела ответа (Полная проверка структуры и типов данных ответа)"):
        resp_json = resp.json()

        # Полная проверка структуры и типов данных ответа
        assert_register_payload(resp_json)

        if saved_name == valid_fullname.strip() + "'s Space":
            pass  # OK, API делает trim
        else:
            assert saved_name == valid_fullname + "'s Space", \
                f"Имя искажено. Отправлено: '{valid_fullname}', Сохранено: '{saved_name}'"


@allure.parent_suite("Auth Service")
@allure.suite("Registration Validation")
@allure.sub_suite("Fullname Validation")
@pytest.mark.parametrize("fullname_value, description", [
    ("a" * (MAX_FULL_NAME_LENGTH + 1), f"Имя длиннее максимума ({MAX_FULL_NAME_LENGTH + 1} симв.)"),
    ("", "Пустое имя"),
    (" ", "Пробел вместо имени")
], ids=["fullname_too_long", "fullname_empty", "fullname_space"])
def test_register_invalid_fullname_length(fullname_value, description, base_url=API_URL):
    """
    Тест валидации граничных значений длины полного имени.
    """
    allure.dynamic.title(f"Register: Валидация длины имени ({description})")

    timestamp = int(time.time())
    user_email = f"name_limit_{timestamp}@gmail.com"
    user_password = "validPass123"

    with allure.step(f"Подготовка данных с именем длины {len(fullname_value)}"):
        endpoint_data = register_endpoint(
            email=user_email,
            password=user_password,
            full_name=fullname_value,
            terms_accepted=True
        )

    with allure.step("Отправка запроса на регистрацию"):
        url = f"{base_url.rstrip('/')}{endpoint_data['path']}"
        resp = requests.post(url, json=endpoint_data['json'], headers=endpoint_data['headers'])

    with allure.step("Проверка отказа (400 Bad Request)"):
        assert resp.status_code == 400, \
            f"Ожидался статус 400, но получен {resp.status_code}. Длина имени: {len(fullname_value)}"

    with allure.step("Проверка, что ошибка относится к fullName"):
        resp_json = resp.json()
        # Ищем 'fullName' или 'full_name' в тексте ошибки
        assert "fullname" in str(resp_json).lower(), "В ошибке не упоминается поле fullName"