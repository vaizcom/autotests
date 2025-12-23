import allure
import pytest
import requests
from tests.config.settings import API_URL, MAIN_SPACE_ID
from tests.test_backend.data.endpoints.Space.space_endpoints import get_space_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Auth Service")
@allure.title("Авторизация: валидный токен и в Authorization и в Cookie - статус 200")
def test_token_valid(owner_client):
    # Используем достоверный эндпоинт
    payload = get_space_endpoint(space_id=MAIN_SPACE_ID)
    with allure.step("POST с валидным токеном к корректному эндпоинту"):
        r = owner_client.post(**payload)
    assert r.status_code != 401, f'Ожидали авторизованный доступ, получили {r.status_code}: {r.text}'
    assert r.status_code != 404, f'Эндпоинт не найден: {payload}'
    with allure.step("Проверка: успешный статус 200"):
        assert r.status_code == 200


@allure.parent_suite("Auth Service")
@allure.title("Авторизация: отсутствие токена (в Authorization и Cookie,) приводит к Unauthorized 401)")
def test_token_missing():
    """
    Проверка универсальна для всех эндпоинтов. Выполнена на GetSpaces.
    """
    url = f'{API_URL}/GetSpaces'
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Content-Type": "application/json",
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

@allure.parent_suite("Auth Service")
@allure.title("Авторизация: невалидный токен приводит к отказу в доступе Bad Request 400")
def test_token_invalid(owner_client):
    """
    Проверка универсальна для всех эндпоинтов. Выполнена на GetSpaces.
    """
    url = f'{API_URL}/GetSpaces'
    invalid = make_invalid_token(owner_client)
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Authorization": f"Bearer {invalid}",
        "Cookie": f"_t={invalid}",
        "Content-Type": "application/json",
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

@allure.parent_suite("Auth Service")
@allure.title("Авторизация: пустой токен '_t=' приводит к Unauthorized 401 ")
def test_token_empty():
    url = f'{API_URL.rstrip("/")}/GetSpaceMembers'
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Cookie": '_t= ',
        "Content-Type": "application/json",
        # Опционально можно не передавать Authorization вовсе
        # "Authorization": "Bearer",
    }
    with allure.step('POST с пустым токеном в Cookie (_t="")'):
        r = requests.post(url, data="", headers=headers)
    with allure.step("Проверка: статус 401 Unauthorized"):
        assert r.status_code == 401, f'Ожидали 401 при пустом токене, получили {r.status_code}; body={r.text}'
        assert r.status_code != 404, f'Эндпоинт не найден: url={url}'
    with allure.step("Проверка структуры тела ошибки"):
        body = r.json()
        assert body.get("payload") is None, "payload должен быть null"
        assert body.get("type") == "GetSpaceMembers", f"type должен быть GetSpaceMembers, получено: {body.get('type')}"
        err = (body or {}).get("error") or {}
        assert err.get("code") == "Unauthorized", f'error.code должен быть "Unauthorized", получено: {err.get("code")}'
        assert err.get("originalType") == "GetSpaceMembers", "error.originalType должен совпадать с типом"

@allure.parent_suite("Auth Service")
@allure.title("Авторизация: токен пользователя без доступа к спейсу (foreign_client) => 400")
def test_token_foreign_client(foreign_client: str):
    url = f'{API_URL.rstrip("/")}/GetSpace'
    token = getattr(foreign_client, "token", "")
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Cookie": f"_t={token}",
        "Content-Type": "application/json",
    }
    payload = {
        "spaceId": MAIN_SPACE_ID
    }
    with allure.step("POST с токеном foreign_client (нет прав к спейсу)"):
        r = requests.post(url, json=payload, headers=headers)
    with allure.step("Проверка: ожидаемый статус код 400"):
        assert r.status_code != 404, f'Эндпоинт не найден: url={url}'
        assert r.status_code == 400, f'Ожидали 400, получили {r.status_code}; body={r.text}'
    with allure.step("Проверка структуры тела ошибки: AccessDenied"):
        body = r.json()
        err = (body or {}).get("error") or {}
        assert body.get("type") == "GetSpace", f"type должен быть GetSpace, получено: {body.get('type')}"
        assert body.get("payload") is None, "payload должен быть null"
        assert err.get("originalType") == "GetSpace", "error.originalType должен совпадать с типом"
        assert err.get("code") == "MemberDidNotFound" , \
            f'Ожидали code MemberDidNotFound, получили: {err.get("code")}'