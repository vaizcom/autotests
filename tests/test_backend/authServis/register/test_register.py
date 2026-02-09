import time
import allure
import requests

from config.settings import API_URL
from test_backend.data.endpoints.User.register_endpoint import register_endpoint


@allure.parent_suite("Auth Service")
@allure.suite("Registration")
def test_register_user_success(base_url=API_URL):
    """
    Тест регистрации нового пользователя с валидными данными.
    """
    allure.dynamic.title("Register: Успешная регистрация пользователя")

    # Генерируем уникальный email используя timestamp
    timestamp = int(time.time())
    user_email = f"autotest_{timestamp}@gmail.com"
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

    with allure.step("Валидация тела ответа"):
        resp_json = resp.json()

        user_data = resp_json.get('payload')

        assert user_data is not None, "В ответе отсутствует payload с данными пользователя"

        # Проверка соответствия отправленных данных
        space_data = user_data.get('space')
        assert space_data is not None, "Объект space отсутствует в ответе"
        assert space_data.get('name') == user_name + "'s Space", "Имя пользователя в ответе не совпадает"

    with allure.step("Проверка безопасности (отсутствие пароля в ответе)"):
        assert 'password' not in user_data, "Критично: Пароль вернулся в ответе сервера!"