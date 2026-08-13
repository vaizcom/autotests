import allure
import pytest
import requests

PUBLIC_API_BASE_URL = "https://api.vaiz.com"

pytestmark = [pytest.mark.public_api]


@allure.parent_suite("Public API")
@allure.suite("Авторизация")
@allure.sub_suite("Negative")
@allure.title("Запрос без токена авторизации возвращает 401")
def test_public_api_no_token(public_space_id):
    """
    Проверяем что без Authorization header любой эндпоинт публичного API возвращает 401.
    """
    with allure.step("Отправляем запрос без токена авторизации"):
        resp = requests.get(
            f"{PUBLIC_API_BASE_URL}/public/v1/history",
            params={"spaceId": public_space_id, "kind": "Space", "kindId": public_space_id},
        )

    with allure.step("Статус ответа 401"):
        assert resp.status_code == 401, \
            f"Ожидался 401, получен {resp.status_code}: {resp.text}"


@allure.parent_suite("Public API")
@allure.suite("Авторизация")
@allure.sub_suite("Negative")
@allure.title("Запрос с невалидным токеном возвращает 401")
def test_public_api_invalid_token(public_space_id):
    """
    Проверяем что с некорректным токеном любой эндпоинт публичного API возвращает 401.
    """
    with allure.step("Отправляем запрос с невалидным токеном"):
        resp = requests.get(
            f"{PUBLIC_API_BASE_URL}/public/v1/history",
            headers={"Authorization": "Bearer invalid_token_12345"},
            params={"spaceId": public_space_id, "kind": "Space", "kindId": public_space_id},
        )

    with allure.step("Статус ответа 401"):
        assert resp.status_code == 401, \
            f"Ожидался 401, получен {resp.status_code}: {resp.text}"
