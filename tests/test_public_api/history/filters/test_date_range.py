import time

import allure
import pytest

from test_public_api.data.endpoints.public_history_endpoint import public_history_endpoint

pytestmark = [pytest.mark.public_api]


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Filters: Positive")
def test_public_history_date_range(public_client, public_space_id):
    """dateRangeStart/dateRangeEnd фильтрует события по дате."""
    allure.dynamic.title("dateRange за пределами данных — пустой items")

    with allure.step("Запрашиваем с dateRangeStart в будущем (2030)"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
                date_range_start="2030-01-01T00:00:00.000Z",
            )
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    with allure.step("items пустой — нет событий в будущем"):
        assert len(resp.json()["items"]) == 0, \
            f"Ожидался пустой items для dateRangeStart=2030, получено {len(resp.json()['items'])}"

    time.sleep(1)

    with allure.step("Запрашиваем с dateRangeEnd в прошлом (2020)"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
                date_range_end="2020-01-01T00:00:00.000Z",
            )
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    with allure.step("items пустой — нет событий до 2020"):
        assert len(resp.json()["items"]) == 0, \
            f"Ожидался пустой items для dateRangeEnd=2020, получено {len(resp.json()['items'])}"


@allure.parent_suite("Public API")
@allure.suite("History")
@allure.sub_suite("Filters: Positive")
def test_public_history_date_range_with_data(public_client, public_space_id):
    """dateRange покрывающий реальные данные возвращает непустой items."""
    allure.dynamic.title("dateRange покрывающий данные — непустой items")

    with allure.step("Запрашиваем с dateRange покрывающим весь день создания спейса"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
                date_range_start="2026-08-12T00:00:00.000Z",
                date_range_end="2026-08-13T00:00:00.000Z",
            )
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    with allure.step("items не пустой"):
        items = resp.json()["items"]
        assert len(items) > 0, "Ожидались события за 2026-08-12"
