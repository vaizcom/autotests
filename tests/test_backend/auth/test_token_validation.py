import allure
import pytest
import requests
from tests.config.settings import API_URL, MAIN_SPACE_ID
from tests.test_backend.data.endpoints.Space.space_endpoints import get_space_endpoint

pytestmark = [pytest.mark.backend]

@allure.title("Авторизация: валидный токен даёт доступ")
def test_token_valid(owner_client):
    # Используем достоверный эндпоинт
    payload = get_space_endpoint(space_id=MAIN_SPACE_ID)
    with allure.step("POST с валидным токеном к корректному эндпоинту"):
        r = owner_client.post(**payload)
    assert r.status_code != 401, f'Ожидали авторизованный доступ, получили {r.status_code}: {r.text}'
    assert r.status_code != 404, f'Эндпоинт не найден: {payload}'
    with allure.step("Проверка: успешный статус 200"):
        assert r.status_code == 200

@allure.title("Авторизация: отсутствие токена приводит к отказу в доступе и 401)")
def test_token_missing():
    """
    Проверка универсальна для всех эндпоинтов. Выполнена на GetSpaces.
    """
    url = f'{API_URL.rstrip("/")}/GetSpaces'
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID
    }
    # Без Authorization и Cookie, пустое тело
    with allure.step("POST без Authorization и Cookie к GetSpaces"):
        r = requests.post(url, data="", headers=headers)
    with allure.step("Проверка: ожидаем отказ в доступе и 401"):
        assert r.status_code == 401, f'Ожидали отказ без токена, получили {r.status_code}; body={r.text}'
        assert r.status_code != 404, f'Эндпоинт не найден: url={url}'



def make_invalid_token(owner_client) -> str:
    token = getattr(owner_client, "token", "")
    assert token, "owner_client.token пуст"
    return token[:-1] + ("0" if token[-1] == "1" else "1")

@allure.title("Авторизация: невалидный токен приводит к отказу в доступе и 400")
def test_token_invalid(owner_client):
    """
    Проверка универсальна для всех эндпоинтов. Выполнена на GetSpaces.
    """
    url = f'{API_URL.rstrip("/")}/GetSpaces'
    invalid = make_invalid_token(owner_client)
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Authorization": f"Bearer {invalid}",
        "Cookie": f"_t={invalid}",
    }
    with allure.step("Отправляем POST-запрос с невалидным токеном"):
        r = requests.post(url, data="", headers=headers)
    with allure.step("Ожидаем отказ в доступе 400"):
        assert r.status_code == 400, f'Ожидали отказ с невалидным токеном, получили {r.status_code}; body={r.text}'
    assert r.status_code != 404, f'Эндпоинт не найден: url={url}'

    # Проверяем meta.token и meta.description, если сервер вернул тело ошибки
    try:
        body = r.json()
    except ValueError:
        pytest.skip("Сервер вернул не-JSON при ошибке, пропускаем проверку meta")

    err = (body or {}).get("error") or {}
    meta = err.get("meta") or {}
    with allure.step("В ответе видим невалидный token, совпадает с отправленным невалидным токеном"):
        assert meta.get("token") == invalid, "В meta.token ожидали отправленный невалидный токен"
    with allure.step('В ответе видим meta.description == "invalid signature"'):
        assert meta.get("description") == "invalid signature", f"Неожиданное описание: {meta.get('description')}"