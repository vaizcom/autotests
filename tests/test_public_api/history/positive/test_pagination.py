import time

import allure
import pytest

from test_public_api.data.endpoints.public_history_endpoint import public_history_endpoint

pytestmark = [pytest.mark.public_api]


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Positive: Pagination")
def test_public_history_limit(public_client, public_space_id):
    """limit ограничивает количество items в ответе."""
    allure.dynamic.title("limit=5 возвращает ровно 5 items и hasMore=true")

    with allure.step("Отправляем запрос с limit=5"):
        resp = public_client.get(
            **public_history_endpoint(space_id=public_space_id, kind="Space", kind_id=public_space_id, limit=5)
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    body = resp.json()

    with allure.step("items содержит ровно 5 элементов"):
        assert len(body["items"]) == 5, f"Ожидалось 5 items, получено {len(body['items'])}"

    with allure.step("hasMore=true — есть ещё данные"):
        assert body["page"]["hasMore"] is True

    with allure.step("nextCursor присутствует"):
        assert isinstance(body["page"]["nextCursor"], int), \
            f"nextCursor должен быть int, получен {body['page'].get('nextCursor')}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Positive: Pagination")
def test_public_history_next_cursor(public_client, public_space_id):
    """nextCursor возвращает следующую страницу без пересечений с предыдущей."""
    allure.dynamic.title("nextCursor возвращает следующую страницу без дубликатов")

    with allure.step("Запрашиваем первую страницу (limit=5)"):
        resp1 = public_client.get(
            **public_history_endpoint(space_id=public_space_id, kind="Space", kind_id=public_space_id, limit=5)
        )
        assert resp1.status_code == 200, f"Страница 1: {resp1.text}"
        page1 = resp1.json()
        assert page1["page"]["hasMore"] is True, "hasMore должен быть true для limit=5"
        cursor = page1["page"]["nextCursor"]

    time.sleep(1)

    with allure.step(f"Запрашиваем вторую страницу (nextCursor={cursor})"):
        resp2 = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
                limit=5, next_cursor=cursor,
            )
        )
        assert resp2.status_code == 200, f"Страница 2: {resp2.text}"
        page2 = resp2.json()

    with allure.step("Вторая страница содержит items"):
        assert len(page2["items"]) > 0, "Вторая страница пустая"

    with allure.step("Нет пересечений между страницами"):
        ids_1 = {item["_id"] for item in page1["items"]}
        ids_2 = {item["_id"] for item in page2["items"]}
        overlap = ids_1 & ids_2
        assert not overlap, f"Дубликаты между страницами: {overlap}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Positive: Pagination")
def test_public_history_limit_exceeds_total(public_client, public_space_id):
    """limit больше общего количества событий — возвращает все items и hasMore=false."""
    allure.dynamic.title("limit=1000 (больше всех событий) — hasMore=false, все items")

    with allure.step("Запрашиваем с limit=1000"):
        resp = public_client.get(
            **public_history_endpoint(space_id=public_space_id, kind="Space", kind_id=public_space_id, limit=1000)
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    body = resp.json()

    with allure.step("hasMore=false — все данные получены"):
        assert body["page"]["hasMore"] is False

    with allure.step("nextCursor отсутствует"):
        assert "nextCursor" not in body["page"], \
            f"nextCursor не должен присутствовать при hasMore=false: {body['page']}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Positive: Pagination")
def test_public_history_limit_one(public_client, public_space_id):
    """limit=1 возвращает ровно 1 item."""
    allure.dynamic.title("limit=1 возвращает ровно 1 item")

    with allure.step("Запрашиваем с limit=1"):
        resp = public_client.get(
            **public_history_endpoint(space_id=public_space_id, kind="Space", kind_id=public_space_id, limit=1)
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    body = resp.json()

    with allure.step("items содержит ровно 1 элемент"):
        assert len(body["items"]) == 1, f"Ожидался 1 item, получено {len(body['items'])}"

    with allure.step("hasMore=true"):
        assert body["page"]["hasMore"] is True


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Negative: Pagination")
@pytest.mark.parametrize("limit_value, expected_code", [
    (0,  "limit must be a positive number"),
    (-1, "limit must be a positive number"),
], ids=["limit_zero", "limit_negative"])
def test_public_history_invalid_limit(public_client, public_space_id, limit_value, expected_code):
    """Невалидный limit (0, отрицательный) возвращает 400."""
    allure.dynamic.title(f"limit={limit_value} возвращает 400 ({expected_code})")

    with allure.step(f"Запрашиваем с limit={limit_value}"):
        resp = public_client.get(
            **public_history_endpoint(space_id=public_space_id, kind="Space", kind_id=public_space_id, limit=limit_value)
        )

    with allure.step(f"Статус 400, ValidationErrors"):
        assert resp.status_code == 400, f"Ожидался 400: {resp.text}"
        body = resp.json()
        assert body["error"]["code"] == "ValidationErrors", f"Ожидался ValidationErrors: {resp.text}"
        field_codes = body["error"]["fields"][0]["codes"]
        assert expected_code in field_codes, f"Ожидался '{expected_code}' в codes: {field_codes}"
