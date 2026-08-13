import allure
import pytest

from test_public_api.data.endpoints.public_history_endpoint import public_history_endpoint

pytestmark = [pytest.mark.public_api]


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Positive")
@allure.title("Валидный запрос возвращает 200 и корректную структуру ответа")
def test_public_history_valid_request(public_client, public_space_id):
    """
    Проверяем базовую доступность эндпоинта:
    - статус 200
    - тело содержит items (список) и page (hasMore + nextCursor при наличии)
    """
    with allure.step("Отправляем GET /public/v1/history с валидными параметрами"):
        resp = public_client.get(
            **public_history_endpoint(space_id=public_space_id, kind="Space", kind_id=public_space_id)
        )

    with allure.step("Статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    body = resp.json()

    with allure.step("Ответ содержит поле 'items'"):
        assert "items" in body, f"Ответ не содержит поле 'items': {body}"

    with allure.step("'items' является списком"):
        assert isinstance(body["items"], list), f"'items' должен быть списком, получен {type(body['items'])}"

    with allure.step("Ответ содержит поле 'page'"):
        assert "page" in body, f"Ответ не содержит поле 'page': {body}"

    page = body["page"]

    with allure.step("'page.hasMore' является булевым"):
        assert isinstance(page.get("hasMore"), bool), \
            f"'page.hasMore' должен быть булевым, получен {page.get('hasMore')}"

    if page["hasMore"]:
        with allure.step("hasMore=true — 'page.nextCursor' присутствует и является int (Unix timestamp)"):
            assert isinstance(page.get("nextCursor"), int), \
                f"'page.nextCursor' должен быть int когда hasMore=true, получен {page.get('nextCursor')}"
    else:
        with allure.step("hasMore=false — 'page.nextCursor' отсутствует"):
            assert "nextCursor" not in page, \
                f"'page.nextCursor' должен отсутствовать когда hasMore=false, получен {page.get('nextCursor')}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Positive")
@allure.title("Элементы items в ответе содержат обязательные поля")
def test_public_history_items_have_required_fields(public_client, public_space_id):
    """
    Проверяем структуру элементов items в ответе:
    - обязательные поля (_id, key, createdAt, type, data, creatorId) присутствуют в каждом элементе
    - источник: интерфейс IHistory
    """
    with allure.step("Отправляем GET /public/v1/history с валидными параметрами"):
        resp = public_client.get(
            **public_history_endpoint(space_id=public_space_id, kind="Space", kind_id=public_space_id)
        )

    with allure.step("Проверяем статус ответа 200"):
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    with allure.step("Проверяем что items не пустой"):
        items = resp.json().get("items", [])
        assert items, "Нет событий в истории спейса — нельзя проверить структуру items"

    with allure.step("Проверяем обязательные поля(_id, key, createdAt, type, data, creatorId) первых 5 элементов"):
        for item in items[:5]:
            for field in ("_id", "key", "createdAt", "type", "data", "creatorId"):
                assert field in item, f"item без поля '{field}': {item}"
