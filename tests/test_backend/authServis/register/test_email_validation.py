import time
import allure
import requests
import pytest

from config.settings import API_URL
from test_backend.data.endpoints.User.register_endpoint import register_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Auth Service")
@allure.suite("Registration")
@pytest.mark.parametrize("invalid_email, description", [
    ("invalid-email-format", "Неверный формат (без @)"),
    ("user name@domain.com", "Пробелы в адресе"),
    ("user@domain", "Отсутствует зона домена (.com)"),
    (" ", "Пустое значение")
], ids=[
    "bad_format",
    "spaces_in_address",
    "incomplete_domain",
    "empty"
])
def test_register_with_invalid_email(invalid_email, description, base_url=API_URL):
    """
    Негативный тест регистрации с некорректным форматом email.
    """
    allure.dynamic.title(f"Register: Отказ при валидации email ({description})")

    # Генерируем остальные данные корректно, чтобы изолировать проверку email
    timestamp = int(time.time())
    user_password = "123456"
    user_name = f"autotest_{timestamp}"

    with allure.step(f"Подготовка данных с невалидным email: {invalid_email}"):
        endpoint_data = register_endpoint(
            email=invalid_email,
            password=user_password,
            full_name=user_name,
            terms_accepted=True
        )

    with allure.step("Отправка POST запроса на регистрацию"):
        url = f"{base_url.rstrip('/')}{endpoint_data['path']}"
        resp = requests.post(
            url,
            json=endpoint_data['json'],
            headers=endpoint_data['headers']
        )

    with allure.step("Проверка, что запрос отклонен"):
        assert resp.status_code == 400, \
            f"Ожидался код 400, но получен {resp.status_code}. Email: {invalid_email}"

    with allure.step("Проверка, что ошибка относится к email"):
        resp_json = resp.json()
        # Проверяем, что в ответе упоминается поле email (защита от ложных срабатываний)
        response_str = str(resp_json).lower()
        assert "email" in response_str, "В ответе об ошибке нет упоминания поля email"


@allure.parent_suite("Auth Service")
@allure.suite("Registration")
def test_register_missing_email_field(base_url=API_URL):
    """
    Тест регистрации без передачи поля email в JSON (обязательное поле).
    """
    allure.dynamic.title("Register: Отказ при отсутствии поля email в запросе")

    timestamp = int(time.time())
    user_password = "123456"
    user_name = f"autotest_{timestamp}"

    with allure.step("Подготовка данных и удаление поля email"):
        # Генерируем валидные данные через эндпоинт
        endpoint_data = register_endpoint(
            email="temp@mail.com",  # Значение не важно, мы удалим поле
            password=user_password,
            full_name=user_name,
            terms_accepted=True
        )

        # Удаляем ключ email из JSON payload
        if 'email' in endpoint_data['json']:
            del endpoint_data['json']['email']

    with allure.step("Отправка POST запроса без email"):
        url = f"{base_url.rstrip('/')}{endpoint_data['path']}"

        resp = requests.post(
            url,
            json=endpoint_data['json'],
            headers=endpoint_data['headers']
        )

    with allure.step("Проверка, что запрос отклонен"):
        assert resp.status_code == 400, \
            f"Ожидался код 400 (Bad Request), но получен {resp.status_code}. Ответ: {resp.text}"

    with allure.step("Проверка сообщения об ошибке"):
        resp_json = resp.json()
        response_str = str(resp_json).lower()
        # Ожидаем, что сервер скажет о пропущенном поле email
        assert "email" in response_str, "В ошибке не упоминается пропущенное поле email"