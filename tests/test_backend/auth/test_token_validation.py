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

@allure.title("Авторизация: валидный токен и в Authorization и в Cookie - статус 200")
def test_token_authorization_cookie(owner_client):
    """
    Негатив: токен есть только в Authorization.
    Выполнено на GetSpaces.
    """
    url = f'{API_URL}/GetSpaces'
    token = getattr(owner_client, "token", "")
    assert token, "owner_client.token должен быть непустым валидным токеном"
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Authorization": f"Bearer {token}",
        "Cookie": f"_t={token}"
    }
    with allure.step("POST с Authorization и с Cookie к GetSpaces (валидный токен)"):
        r = requests.post(url, data="", headers=headers)
    with allure.step("Проверка: отсутствие 404 и статус 200 (если политика сервиса требует оба источника)"):
        assert r.status_code != 404, f'Эндпоинт не найден: url={url}'
        assert r.status_code ==200, f'Неожиданный статус {r.status_code}'


@allure.title("Авторизация: валидный токен только в Authorization без Cookie - статус 200")
def test_token_only_in_authorization(owner_client):
    """
    Негатив: токен есть только в Authorization.
    Выполнено на GetSpaces.
    """
    url = f'{API_URL}/GetSpaces'
    token = getattr(owner_client, "token", "")
    assert token, "owner_client.token должен быть непустым валидным токеном"
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Authorization": f"Bearer {token}",
        # без Cookie
    }
    with allure.step("POST только с Authorization без Cookie к GetSpaces (валидный токен)"):
        r = requests.post(url, data="", headers=headers)
    with allure.step("Проверка: 200 статус (политика сервиса требует один из источников)"):
        assert r.status_code != 404, f'Эндпоинт не найден: url={url}'
        assert r.status_code ==200, f'Неожиданный статус {r.status_code}'

@allure.title("Авторизация: валидный токен только в Cookie без Authorization - статус 200")
def test_token_only_in_cookie(owner_client):
    """
    Негатив: токен есть только в Cookie.
    Выполнено на GetSpaces.
    """
    url = f'{API_URL}/GetSpaces'
    token = getattr(owner_client, "token", "")
    assert token, "owner_client.token должен быть непустым валидным токеном"
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Cookie": f"_t={token}",
        # без Authorization
    }
    with allure.step("POST только с Cookie без Authorization к GetSpaces (валидный токен)"):
        r = requests.post(url, data="", headers=headers)
    with allure.step("Проверка: 200 статус (политика сервиса требует один из источников)"):
        assert r.status_code != 404, f'Эндпоинт не найден: url={url}'
        assert r.status_code == 200, f'Неожиданный статус {r.status_code}'

@allure.title("Авторизация: отсутствие токена (Без Authorization и Cookie,) приводит к отказу в доступе и 401)")
def test_token_missing():
    """
    Проверка универсальна для всех эндпоинтов. Выполнена на GetSpaces.
    """
    url = f'{API_URL}/GetSpaces'
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
    url = f'{API_URL}/GetSpaces'
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

@allure.title("Авторизация: пустой токен '_t=' приводит к Unauthorized 401 ")
@allure.description(
    "Негативная проверка: передача пустого токена в Authorization и Cookie должна завершаться отказом Unauthorized 401. "
    "Универсальна для всех эндпоинтов; выполнена на GetSpaceMembers."
)
def test_token_empty():
    url = f'{API_URL.rstrip("/")}/GetSpaceMembers'
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Cookie": '_t=',
        # Опционально можно не передавать Authorization вовсе
        # "Authorization": "Bearer",
    }
    with allure.step('POST с пустым токеном в Cookie (_t="")'):
        r = requests.post(url, data="", headers=headers)
    with allure.step("Проверка: статус 401 Unauthorized"):
        assert r.status_code == 401, f'Ожидали 401 при пустом токене, получили {r.status_code}; body={r.text}'
    with allure.step("Проверка: нет 404 (эндпоинт существует)"):
        assert r.status_code != 404, f'Эндпоинт не найден: url={url}'
    with allure.step("Проверка структуры тела ошибки"):
        body = r.json()
        assert body.get("payload") is None, "payload должен быть null"
        assert body.get("type") == "GetSpaceMembers", f"type должен быть GetSpaceMembers, получено: {body.get('type')}"
        err = (body or {}).get("error") or {}
        assert err.get("code") == "Unauthorized", f'error.code должен быть "Unauthorized", получено: {err.get("code")}'
        assert err.get("originalType") == "GetSpaceMembers", "error.originalType должен совпадать с типом"

@allure.title("Авторизация: токен пользователя без доступа к спейсу (foreign_client) => отказ 400")
@allure.description(
    "Негативная проверка: токен существующего клиента, не имеющего доступа к текущему пространству, "
    "должен приводить к 400 Bad Request без 404. Универсальна; выполнена на GetSpaceMembers."
)
def test_token_foreign_client(foreign_client: str):
    url = f'{API_URL.rstrip("/")}/GetSpaceMembers'
    token = foreign_client
    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Cookie": f"_t={token}",
    }
    with allure.step("POST с токеном foreign_client (нет прав к спейсу)"):
        r = requests.post(url, data="", headers=headers)
    with allure.step("Проверка: отсутствие 404"):
        assert r.status_code != 404, f'Эндпоинт не найден: url={url}'
    with allure.step("Проверка структуры тела ошибки: допускаем SpaceIdNotSpecified или JwtIncorrect"):
        body = r.json()
        err = (body or {}).get("error") or {}
        assert body.get("type") == "GetSpaceMembers", f"type должен быть GetSpaceMembers, получено: {body.get('type')}"
        assert body.get("payload") is None, "payload должен быть null"
        assert err.get("originalType") == "GetSpaceMembers", "error.originalType должен совпадать с типом"
        assert err.get("code") in ("SpaceIdNotSpecified", "JwtIncorrect"), \
            f'Ожидали code SpaceIdNotSpecified или JwtIncorrect, получили: {err.get("code")}'


@allure.title("Авторизация: logout инвалидирует текущий токен (до — 200, после — 400/401)")
def test_logout_invalidates_token(owner_client):
    """
    Сценарий:
    1) До logout: защищённый эндпоинт доступен (200).
    2) POST /Logout с пустым телом {}.
    3) После logout: тот же токен получает отказ 400/401 (JwtDoesNotExits/JwtIncorrect/Unauthorized).
    """
    url_members = f'{API_URL}/GetSpaceMembers'
    url_logout = f'{API_URL}/Logout'

    token = getattr(owner_client, "token", "")
    assert token, "owner_client.token пуст"

    headers = {
        "Current-Space-Id": MAIN_SPACE_ID,
        "Authorization": f"Bearer {token}",
        "Cookie": f"_t={token}",
        "Content-Type": "application/json",
    }

    with allure.step("До logout: доступ к защищённому эндпоинту (ожидаем 200)"):
        r = requests.post(url_members, data="", headers=headers)
    assert r.status_code != 404, f'Эндпоинт не найден: url={url_members}'
    assert r.status_code == 200, f'Ожидали 200 до logout, получили {r.status_code}; body={r.text}'

    with allure.step("Вызываем Logout с пустым телом {}"):
        r = requests.post(url_logout, json={}, headers=headers)
    assert r.status_code != 404, f'Эндпоинт Logout не найден: url={url_logout}'
    # Успешный logout: 200
    assert r.status_code == 200, f'Неожиданный статус logout: {r.status_code}; body={r.text}'

    with allure.step("После logout: тот же токен должен быть невалиден (ожидаем 400/401)"):
        r = requests.post(url_members, data="", headers=headers)
    assert r.status_code != 404, f'Эндпоинт не найден: url={url_members}'
    assert r.status_code == 400, f'Ожидали 400/401 после logout, получили {r.status_code}; body={r.text}'
    try:
        body = r.json()
    except ValueError:
        pytest.skip("Сервер вернул не-JSON при ошибке после logout, пропускаем проверку кода")
    err = (body or {}).get("error") or {}
    assert err.get("code") == "JwtDoesNotExits", \
        f'Ожидали JwtDoesNotExits/JwtIncorrect/Unauthorized, получили: {err.get("code")}'