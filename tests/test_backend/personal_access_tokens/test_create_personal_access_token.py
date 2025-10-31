import pytest
import allure
import re
from datetime import datetime

from test_backend.data.endpoints.personal_access_tokens.pat_edpoints import create_token

pytestmark = [pytest.mark.backend]


@allure.title("Создание персонального access-токена (уникальное имя, полное покрытие требований)")
def test_create_personal_access_token(owner_client, main_space):
    token_name = f"api_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    response = create_token(owner_client.token, main_space, token_name)

    with allure.step("Проверяем HTTP-статус"):
        assert response.status_code == 200, f"Статус: {response.status_code}, текст: {response.text}"

    data = response.json()

    with allure.step("Проверяем структуру ответа и обязательные ключи"):
        assert isinstance(data, dict)
        assert "payload" in data
        assert "type" in data and data["type"] == "CreatePersonalAccessToken"

    payload = data["payload"]

    with allure.step("plainTextToken — есть, формат верный"):
        assert "plainTextToken" in payload, "Нет plainTextToken в payload"
        plain_token = payload["plainTextToken"]
        assert isinstance(plain_token, str)
        assert plain_token.startswith("pat_"), "plainTextToken должен начинаться с pat_"
        hex_part = plain_token[4:]
        assert re.fullmatch(r"[0-9a-f]{64}", hex_part), "plainTextToken после pat_ должен быть 64 hex-символа"

    with allure.step("hashedToken отсутствует"):
        assert "hashedToken" not in payload, "Поле hashedToken не должно присутствовать в ответе"

    with allure.step("Проверяем объект token и его ключи"):
        assert "token" in payload
        token_obj = payload["token"]
        for field in ["_id", "name", "user", "createdAt", "updatedAt"]:
            assert field in token_obj, f"Нет поля {field} в token"
        assert token_obj["name"] == token_name, "Название токена не соответствует"
        assert "lastUsedAt" in token_obj
        assert token_obj["lastUsedAt"] is None or isinstance(token_obj["lastUsedAt"], str)


@allure.title("Создание двух токенов с одинаковым именем (дубликаты разрешены)")
def test_create_duplicate_personal_access_token(owner_client, main_space):
    token_name = f"api_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"

    with allure.step("Создаём первый токен"):
        resp1 = create_token(owner_client.token, main_space, token_name)
        assert resp1.status_code == 200, f"Первый: {resp1.status_code} {resp1.text}"
        data1 = resp1.json()
        token_id1 = data1["payload"]["token"]["_id"]
        plain_token1 = data1["payload"]["plainTextToken"]

    with allure.step("Создаём дубликат (второй токен с тем же именем)"):
        resp2 = create_token(owner_client.token, main_space, token_name)
        assert resp2.status_code == 200, f"Второй: {resp2.status_code} {resp2.text}"
        data2 = resp2.json()
        token_id2 = data2["payload"]["token"]["_id"]
        plain_token2 = data2["payload"]["plainTextToken"]

    with allure.step("Токены должны отличаться по _id и plainTextToken"):
        assert token_id1 != token_id2, "ID токенов совпадают — должны быть разные!"
        assert plain_token1 != plain_token2, "plainTextToken совпадают — должны быть разные!"


@allure.title("Попытка создать персональный access-токен с пустым name — ожидается ошибка")
def test_create_token_with_empty_name(owner_client, main_space):
    with allure.step("Отправляем запрос с пустым name"):
        response = create_token(owner_client.token, main_space, "")
        assert response.status_code == 400, f"Ожидался статус 400, получен: {response.status_code}"

    with allure.step("Проверяем структуру ошибки и коды ошибок"):
        data = response.json()
        error = data.get("error", {})
        assert error.get("code") == "InvalidForm", f'code: {error.get("code")}'
        # Проверяем наличие ошибки по полю name
        name_field_codes = []
        for field in error.get("fields", []):
            if field.get("name") == "name":
                name_field_codes = field.get("codes", [])
                break
        assert field, "Нет ошибок по полю name"
        assert (
            "TOKEN_NAME_REQUIRED" in name_field_codes or "'TOKEN_NAME_REQUIRED'" in name_field_codes
        ), f"Не найден нужный код ошибки в name_field_codes: {name_field_codes}"

@allure.title("Проверка ограничений длины поля name при создании токена")
@pytest.mark.parametrize(
    "token_name, expected_status",
    [
        ("x" * 100, 200),
        ("x" * 101, 400),
    ],
    ids=["ровно 100 символов", "101 символ (слишком длинное имя)"]
)
def test_token_name_length_limit(owner_client, main_space, token_name, expected_status):
    with allure.step(f"Пробуем создать токен с длиной name = {len(token_name)}"):
        response = create_token(owner_client.token, main_space, token_name)
        assert response.status_code == expected_status, f"status code: {response.status_code}, text: {response.text}"

    if expected_status == 400:
        with allure.step("Проверка ошибки валидации длины name"):
            data = response.json()
            error = data.get("error", {})
            assert error.get("code") == "InvalidForm"
            name_codes = []
            for field in error.get("fields", []):
                if field.get("name") == "name":
                    name_codes = field.get("codes", [])
                    break
            assert name_codes, "Нет ошибок по полю name"
            assert (
                "TOKEN_NAME_TOO_LONG" in name_codes
            ), f"Ожидался код 'TOKEN_NAME_TOO_LONG', получены: {name_codes}"


@allure.title("Лимит создания токенов: 1 успешный, затем не более 5 попыток до 429")
def test_token_creation_limit_and_limited_after(owner_client, main_space):
    # Первый токен — успешный
    with allure.step("Создание первого токена (ожидаем 200)"):
        resp1 = create_token(owner_client.token, main_space, "limit_dynamic_1")
        if resp1.status_code != 200:
            data = resp1.json()
            error = data.get("error", {})
            if error.get("code") == "AccessDenied" and error.get("meta", {}).get("rateLimitExceeded") is True:
                pytest.skip("Лимит токенов был превышен до запуска теста.")
            else:
                pytest.fail(f"Непредвиденный ответ: {resp1.status_code}, text: {resp1.text}")

    # Цикл из максимум 5 попыток, ожидаем получить 429 на одной из них
    got_429 = False
    for i in range(2, 7):  # 2,3,4,5,6 — всего 5 попыток после первого
        with allure.step(f"Создание токена №{i} — в одной из попыток должен прийти лимит (429)"):
            resp = create_token(owner_client.token, main_space, f"limit_dynamic_{i}")
            if resp.status_code in (400, 429):
                data = resp.json()
                error = data.get("error", {})
                if error.get("code") == "AccessDenied" and error.get("meta", {}).get("rateLimitExceeded") is True:
                    got_429 = True
                    break
                else:
                    pytest.fail(f"Неожиданная ошибка: {resp.status_code}, {resp.text}")
            elif resp.status_code == 200:
                continue
            else:
                pytest.fail(f"Неожиданный код: {resp.status_code}, текст: {resp.text}")

    assert got_429, "Ни одна из 5 попыток не вернула лимит (429/AccessDenied/rateLimitExceeded)"