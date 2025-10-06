import pytest
import allure
from test_backend.data.endpoints.personal_access_tokens.pat_edpoints import get_tokens

pytestmark = [pytest.mark.backend]


@allure.title("Успешный запрос возвращает список токенов. Каждый элемент содержит id, name, createdAt, но не содержит hashedToken.")
def test_get_personal_access_tokens(owner_client, main_space):
    with allure.step("Отправляем запрос на получение списка токенов"):
        response = get_tokens(owner_client.token, main_space)
        assert response.status_code == 200, f"Статус: {response.status_code}, текст: {response.text}"

    data = response.json()
    with allure.step("Проверяем структуру ответа"):
        assert isinstance(data, dict), "Ответ должен быть dict"
        assert "payload" in data, "Нет ключа payload"
        payload = data["payload"]
        assert isinstance(payload, dict), "payload должен быть dict"
        assert "tokens" in payload, "В payload нет ключа tokens"
        tokens = payload["tokens"]
        assert isinstance(tokens, list), "payload['tokens'] не список"

    if not tokens:
        pytest.skip("Нет токенов у пользователя, чтобы проверить структуру элементов.")

    with allure.step("Проверяем обязательные поля у всех токенов"):
        for token in tokens:
            assert isinstance(token, dict), "Токен в списке не dict"
            assert "_id" in token, "Нет поля _id в токене"
            assert "name" in token, "Нет поля name в токене"
            assert "createdAt" in token, "Нет поля createdAt в токене"
            assert "hashedToken" not in token, "Поле hashedToken НЕ должно присутствовать в выдаче"
