import uuid
from datetime import datetime

import pytest
import allure
from test_backend.data.endpoints.personal_access_tokens.pat_edpoints import get_tokens, delete_personal_access_token, \
    create_token

pytestmark = [pytest.mark.backend]


@allure.title("Создать токен, убедиться что он есть среди полученных, удалить все токены и убедиться что список пуст")
def test_create_and_delete_personal_access_tokens(owner_client, main_space):
    # 1. Создание одного токена
    token_name = f"test_single_{datetime.now().strftime('%H%M%S')}"
    with allure.step("Создаем access-токен"):
        resp = create_token(owner_client.token, main_space, token_name)
        assert resp.status_code == 200, f"Не удалось создать токен: {resp.text}"

    # 2. Получение всех токенов
    with allure.step("Получаем список всех токенов"):
        response = get_tokens(owner_client.token, main_space)
        assert response.status_code == 200, "Ошибка при получении токенов"
        data = response.json()
        tokens = data["payload"]["tokens"]
        assert isinstance(tokens, list), "payload['tokens'] не список"

    # 3. Находим id только что созданного токена
    created_ids = [t["_id"] for t in tokens if t["name"] == token_name]
    assert len(created_ids) == 1, f"Созданный токен не найден, tokens = {tokens}"
    created_token_id = created_ids[0]

    # Дополнительно: соберём все id токенов для удаления
    all_token_ids = [t["_id"] for t in tokens]

    # 4. Удаляем все токены
    with allure.step("Удаляем все токены"):
        for token_id in all_token_ids:
            del_resp = delete_personal_access_token(owner_client.token, main_space, token_id)
            assert del_resp.status_code == 200, f"Не удалось удалить токен {token_id}: {del_resp.text}"

    # 5. Проверяем, что теперь список токенов пуст
    with allure.step("Проверяем, что список токенов пуст"):
        response2 = get_tokens(owner_client.token, main_space)
        assert response2.status_code == 200
        tokens2 = response2.json()["payload"]["tokens"]
        assert tokens2 == [], f"Список токенов после удаления НЕ пуст: {tokens2}"


@allure.title("Повторное удаление одного токена возвращает корректную ошибку (например, 404 Not Found)")
def test_delete_personal_access_token_twice(owner_client, main_space):
    # 1. Создать токен
    token_name = f"double_delete_{datetime.now().strftime('%H%M%S')}"
    with allure.step("Создаем access-токен"):
        resp = create_token(owner_client.token, main_space, token_name)
        assert resp.status_code == 200, f"Не удалось создать токен: {resp.text}"
        token_id = resp.json()["payload"]["token"]["_id"]

    # 2. Удалить токен (первый раз)
    with allure.step("Удаляем токен впервые"):
        del_resp = delete_personal_access_token(owner_client.token, main_space, token_id)
        assert del_resp.status_code == 200, f"Первое удаление не прошло: {del_resp.text}"

    # 3. Попробовать удалить токен снова
    with allure.step("Пробуем удалить токен повторно — ожидаем ошибку"):
        del_resp2 = delete_personal_access_token(owner_client.token, main_space, token_id)
        assert del_resp2.status_code == 403, (
            f"Ожидался статус 404 для повторного удаления, а был {del_resp2.status_code}: {del_resp2.text}"
        )

@allure.title("Попытка удалить несуществующий токен возвращает корректную ошибку (например, 404 Not Found)")
def test_delete_not_exists_personal_access_token(owner_client, main_space):
    # Генерируем случайный (несуществующий) ID токена
    fake_token_id = str(uuid.uuid4())

    with allure.step(f"Пробуем удалить несуществующий токен с id {fake_token_id} — ожидаем ошибку"):
        del_resp = delete_personal_access_token(owner_client.token, main_space, fake_token_id)
        assert del_resp.status_code == 400, (
            f"Ожидался статус 404, но был {del_resp.status_code}: {del_resp.text}"
        )


@allure.title("Проверка прав: удалить персональный токен может только владелец токена")
def test_delete_token_access_rights(owner_client, member_client, main_space):
    token_name = f"only_owner_delete_{datetime.now().strftime('%H%M%S')}"
    with allure.step("Владелец создает токен"):
        resp = create_token(owner_client.token, main_space, token_name)
        assert resp.status_code == 200, f"Ошибка при создании токена: {resp.text}"
        token_id = resp.json()["payload"]["token"]["_id"]

    with allure.step("Пытаемся удалить токен не-владельцем (member) – ожидаем ошибку доступа"):
        wrong_del_resp = delete_personal_access_token(member_client.token, main_space, token_id)
        assert wrong_del_resp.status_code == 403, (
            f"Ожидался статус 403 или 404, но был {wrong_del_resp.status_code}: {wrong_del_resp.text}"
        )

    with allure.step("Владелец удаляет токен – операция успешна"):
        owner_del_resp = delete_personal_access_token(owner_client.token, main_space, token_id)
        assert owner_del_resp.status_code == 200, (
            f"Владелец не смог удалить токен: {owner_del_resp.status_code} {owner_del_resp.text}"
        )