import allure
import pytest

from test_public_api.data.endpoints.public_history_endpoint import public_history_endpoint

pytestmark = [pytest.mark.public_api]


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.title("GET /public/v1/history — smoke: валидный запрос возвращает 200 с корректной структурой")
def test_public_history_smoke(public_client, public_space_id):
    """
    Базовый smoke-тест: валидный запрос с kind=Space возвращает 200
    и ответ содержит корректную структуру (items, page.hasMore, page.nextCursor).

    Формат ответа публичного API отличается от внутреннего:
    - нет обёртки payload
    - пагинация через page.hasMore + page.nextCursor (Unix timestamp в мс)
    - nextCursor присутствует только если hasMore=true
    """
    resp = public_client.get(
        **public_history_endpoint(space_id=public_space_id, kind="Space", kind_id=public_space_id)
    )

    assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    body = resp.json()

    with allure.step("Проверяем наличие поля 'items'"):
        assert "items" in body, f"Ответ не содержит поле 'items': {body}"
        assert isinstance(body["items"], list), f"'items' должен быть списком, получен {type(body['items'])}"

    with allure.step("Проверяем структуру поля 'page'"):
        assert "page" in body, f"Ответ не содержит поле 'page': {body}"
        page = body["page"]
        assert isinstance(page.get("hasMore"), bool), \
            f"'page.hasMore' должен быть булевым, получен {page.get('hasMore')}"

    with allure.step("Проверяем nextCursor в зависимости от hasMore"):
        if page["hasMore"]:
            assert isinstance(page.get("nextCursor"), int), \
                f"'page.nextCursor' должен быть int (Unix timestamp) когда hasMore=true, получен {page.get('nextCursor')}"
        else:
            assert "nextCursor" not in page, \
                f"'page.nextCursor' должен отсутствовать когда hasMore=false, получен {page.get('nextCursor')}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.title("GET /public/v1/history — структура элементов items")
def test_public_history_item_structure(public_client, public_space_id):
    """
    Проверяем, что каждый элемент items содержит обязательные поля.

    Источник: интерфейс IHistory в packages/shared/src/models/history/types.ts.
    Поля без ? — обязательные, всегда присутствуют: _id, key, createdAt, type, data, creatorId.
    Поля с ? — опциональные, зависят от типа события: memberId, spaceId, projectId,
    boardId, taskId, documentId, milestoneId.

    Набор полей одинаковый для публичного и внутреннего API — бэкенд не скрывает
    и не фильтрует поля истории перед отдачей (в отличие от, например, Document API,
    который скрывает поля space и content).
    """
    resp = public_client.get(
        **public_history_endpoint(space_id=public_space_id, kind="Space", kind_id=public_space_id)
    )
    assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}: {resp.text}"

    items = resp.json().get("items", [])
    assert items, "Нет событий в истории спейса — нельзя проверить структуру items"

    with allure.step(f"Проверяем структуру каждого из {len(items)} элементов"):
        for item in items:
            for field in ("_id", "key", "createdAt", "type", "data", "creatorId"):
                assert field in item, f"item без поля '{field}': {item}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.title("GET /public/v1/history — отсутствие обязательного параметра возвращает 400")
@pytest.mark.parametrize("missing_param", ["spaceId", "kind", "kindId"],
                         ids=["missing_spaceId", "missing_kind", "missing_kindId"])
def test_public_history_missing_required_params(public_client, public_space_id, missing_param):
    """
    При отсутствии любого обязательного параметра (spaceId, kind, kindId)
    публичный API должен вернуть 400.
    """
    params = {"spaceId": public_space_id, "kind": "Space", "kindId": public_space_id}
    params.pop(missing_param)

    resp = public_client.get("/public/v1/history", params=params)

    assert resp.status_code == 400, \
        f"Ожидался 400 при отсутствии '{missing_param}', получен {resp.status_code}: {resp.text}"
