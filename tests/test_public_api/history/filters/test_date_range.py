import time

import allure
import pytest

from test_public_api.data.endpoints.public_history_endpoint import public_history_endpoint

pytestmark = [
    pytest.mark.public_api,
    allure.parent_suite("Public API"),
    allure.suite("History"),
    allure.sub_suite("Date Range"),
]


# ---------------------------------------------------------------------------
# kind=Space
# ---------------------------------------------------------------------------


def test_public_history_date_range_empty(public_client, public_space_id):
    """dateRangeStart в будущем / dateRangeEnd в прошлом — пустой items."""
    allure.dynamic.title("[Space] dateRange за пределами данных — пустой items")

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



def test_public_history_date_range_equal(public_client, public_space_id):
    """dateRangeStart == dateRangeEnd — нулевой интервал, пустой items.

    API использует полуоткрытый интервал [start, end).
    Когда start == end, условие start <= T < start невозможно — пустой результат корректен.
    """
    allure.dynamic.title("[Space] dateRangeStart == dateRangeEnd — пустой items")

    with allure.step("Запрашиваем с dateRangeStart == dateRangeEnd (08-14)"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
                date_range_start="2026-08-14T00:00:00.000Z",
                date_range_end="2026-08-14T00:00:00.000Z",
            )
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    with allure.step("items пустой — нулевой интервал"):
        assert len(resp.json()["items"]) == 0, \
            f"Ожидался пустой items, получено {len(resp.json()['items'])}"



@pytest.mark.xfail(
    reason="BUG: сервер возвращает 200 вместо 400 при start > end — клиент не узнаёт об ошибке",
    strict=True,
)
def test_public_history_date_range_start_after_end(public_client, public_space_id):
    """dateRangeStart > dateRangeEnd — дата начала позже даты конца.

    Сейчас сервер возвращает 200 + пустой items, но ожидается 400 —
    клиент явно ошибся, лучше сообщить об этом чем молча вернуть пустоту.
    """
    allure.dynamic.title("[Space][Negative] dateRangeStart > dateRangeEnd → 400")

    with allure.step("Запрашиваем с dateRangeStart > dateRangeEnd"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
                date_range_start="2026-08-15T00:00:00.000Z",
                date_range_end="2026-08-12T00:00:00.000Z",
            )
        )

    with allure.step("Статус 400 — перевёрнутый интервал невалиден"):
        assert resp.status_code == 400, \
            f"Ожидался 400, получен {resp.status_code}: {resp.text}"



@pytest.mark.parametrize("invalid_date", [
    pytest.param("not-a-date", id="text"),
    pytest.param("", id="empty"),
    pytest.param("10.08.2026", id="dot_format",
                 marks=pytest.mark.xfail(
                     reason="BUG: сервер возвращает 200 вместо 400 для невалидного формата даты",
                     strict=True,
                 )),
    pytest.param("08-10-2026", id="us_format",
                 marks=pytest.mark.xfail(
                     reason="BUG: сервер парсит через JS Date вместо валидации ISO 8601",
                     strict=True,
                 )),
    pytest.param("2026/08/10", id="slash_format",
                 marks=pytest.mark.xfail(
                     reason="BUG: сервер парсит через JS Date вместо валидации ISO 8601",
                     strict=True,
                 )),
    pytest.param("123", id="numeric",
                 marks=pytest.mark.xfail(
                     reason="BUG: сервер парсит число как unix ms вместо валидации ISO 8601",
                     strict=True,
                 )),
])
def test_public_history_date_range_invalid_format(public_client, public_space_id, invalid_date):
    """Невалидный формат даты — 400.

    API принимает только ISO 8601 (2026-08-14T00:00:00.000Z).
    Другие форматы должны возвращать 400 ValidationErrors.
    """
    allure.dynamic.title(f"[Space][Negative] dateRangeStart='{invalid_date}' → 400")

    with allure.step(f"Запрашиваем с dateRangeStart='{invalid_date}'"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
                date_range_start=invalid_date,
            )
        )

    with allure.step("Статус 400, ValidationErrors"):
        assert resp.status_code == 400, f"Ожидался 400: {resp.text}"
        body = resp.json()
        assert body["error"]["code"] == "ValidationErrors", f"Ожидался ValidationErrors: {resp.text}"



def test_public_history_date_range_interval(public_client, public_space_id):
    """dateRange [start, end) — items внутри интервала, нет items вне."""
    allure.dynamic.title("[Space] dateRange [08-12, 08-14) — start включительно, end исключительно")

    start = "2026-08-12T00:00:00.000Z"
    end = "2026-08-14T00:00:00.000Z"

    with allure.step(f"Запрашиваем с dateRangeStart={start}, dateRangeEnd={end}"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
                date_range_start=start, date_range_end=end,
            )
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    items = resp.json()["items"]

    with allure.step("items не пустой"):
        assert len(items) > 0, "Ожидались события в интервале [08-12, 08-14)"

    with allure.step("Все items имеют createdAt >= start (включительно)"):
        before_start = [item for item in items if item["createdAt"] < "2026-08-12T00:00:00"]
        assert len(before_start) == 0, (
            f"{len(before_start)} событий до start: "
            f"{[item['createdAt'] for item in before_start[:5]]}"
        )

    with allure.step("Все items имеют createdAt < end (исключительно)"):
        after_end = [item for item in items if item["createdAt"] >= "2026-08-14T00:00:00"]
        assert len(after_end) == 0, (
            f"{len(after_end)} событий >= end: "
            f"{[item['createdAt'] for item in after_end[:5]]}"
        )

    time.sleep(1)

    with allure.step("Проверяем что за пределами интервала есть события (фильтр реально отсёк)"):
        resp_all = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
            )
        )
        assert resp_all.status_code == 200
        all_items = resp_all.json()["items"]
        outside = [item for item in all_items if item["createdAt"] >= "2026-08-14T00:00:00"]
        assert len(outside) > 0, (
            "Нет событий за пределами интервала — тест не доказывает что end отсекает"
        )



def test_public_history_date_range_start_only(public_client, public_space_id):
    """Только dateRangeStart — все items >= start."""
    allure.dynamic.title("[Space] dateRangeStart=08-14 — все items >= start")

    start = "2026-08-14T00:00:00.000Z"

    with allure.step(f"Запрашиваем с dateRangeStart={start}"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
                date_range_start=start,
            )
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    items = resp.json()["items"]

    with allure.step("items не пустой"):
        assert len(items) > 0, f"Ожидались события после {start}"

    with allure.step("Все items имеют createdAt >= dateRangeStart"):
        before_start = [item for item in items if item["createdAt"] < "2026-08-14T00:00:00"]
        assert len(before_start) == 0, (
            f"{len(before_start)} событий до dateRangeStart: "
            f"{[item['createdAt'] for item in before_start[:5]]}"
        )



def test_public_history_date_range_end_only(public_client, public_space_id):
    """Только dateRangeEnd — все items < end."""
    allure.dynamic.title("[Space] dateRangeEnd=08-15 — все items < end")

    end = "2026-08-15T00:00:00.000Z"

    with allure.step(f"Запрашиваем с dateRangeEnd={end}"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Space", kind_id=public_space_id,
                date_range_end=end,
            )
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    items = resp.json()["items"]

    with allure.step("items не пустой"):
        assert len(items) > 0, f"Ожидались события до {end}"

    with allure.step("Все items имеют createdAt < dateRangeEnd"):
        after_end = [item for item in items if item["createdAt"] >= "2026-08-15T00:00:00"]
        assert len(after_end) == 0, (
            f"{len(after_end)} событий после dateRangeEnd: "
            f"{[item['createdAt'] for item in after_end[:5]]}"
        )


# ---------------------------------------------------------------------------
# kind=Project
# ---------------------------------------------------------------------------


def test_public_history_date_range_project_interval(public_client, public_space_id, demo_project_id):
    """dateRange [start, end) для kind=Project."""
    allure.dynamic.title("[Project] dateRange [08-12, 08-14) — start включительно, end исключительно")

    start = "2026-08-12T00:00:00.000Z"
    end = "2026-08-14T00:00:00.000Z"

    with allure.step(f"Запрашиваем с kind=Project, dateRangeStart={start}, dateRangeEnd={end}"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Project", kind_id=demo_project_id,
                date_range_start=start, date_range_end=end,
            )
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    items = resp.json()["items"]

    with allure.step("items не пустой"):
        assert len(items) > 0, "Ожидались события в интервале [08-12, 08-14) в Project"

    with allure.step("Все items имеют createdAt >= start"):
        before_start = [item for item in items if item["createdAt"] < "2026-08-12T00:00:00"]
        assert len(before_start) == 0, (
            f"{len(before_start)} событий до start: "
            f"{[item['createdAt'] for item in before_start[:5]]}"
        )

    with allure.step("Все items имеют createdAt < end"):
        after_end = [item for item in items if item["createdAt"] >= "2026-08-14T00:00:00"]
        assert len(after_end) == 0, (
            f"{len(after_end)} событий >= end: "
            f"{[item['createdAt'] for item in after_end[:5]]}"
        )

    time.sleep(1)

    with allure.step("Проверяем что за пределами интервала есть события (фильтр реально отсёк)"):
        resp_all = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Project", kind_id=demo_project_id,
            )
        )
        assert resp_all.status_code == 200
        all_items = resp_all.json()["items"]
        outside = [item for item in all_items if item["createdAt"] >= "2026-08-14T00:00:00"]
        assert len(outside) > 0, (
            "Нет событий за пределами интервала — тест не доказывает что end отсекает"
        )



def test_public_history_date_range_project_start_only(public_client, public_space_id, demo_project_id):
    """Только dateRangeStart для kind=Project — все items >= start."""
    allure.dynamic.title("[Project] dateRangeStart=08-14 — все items >= start")

    start = "2026-08-14T00:00:00.000Z"

    with allure.step(f"Запрашиваем с kind=Project, dateRangeStart={start}"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Project", kind_id=demo_project_id,
                date_range_start=start,
            )
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    items = resp.json()["items"]

    with allure.step("items не пустой"):
        assert len(items) > 0, f"Ожидались события после {start}"

    with allure.step("Все items имеют createdAt >= dateRangeStart"):
        before_start = [item for item in items if item["createdAt"] < "2026-08-14T00:00:00"]
        assert len(before_start) == 0, (
            f"{len(before_start)} событий до dateRangeStart: "
            f"{[item['createdAt'] for item in before_start[:5]]}"
        )



def test_public_history_date_range_project_end_only(public_client, public_space_id, demo_project_id):
    """Только dateRangeEnd для kind=Project — все items < end."""
    allure.dynamic.title("[Project] dateRangeEnd=08-15 — все items < end")

    end = "2026-08-15T00:00:00.000Z"

    with allure.step(f"Запрашиваем с kind=Project, dateRangeEnd={end}"):
        resp = public_client.get(
            **public_history_endpoint(
                space_id=public_space_id, kind="Project", kind_id=demo_project_id,
                date_range_end=end,
            )
        )

    with allure.step("Статус 200"):
        assert resp.status_code == 200, f"Ожидался 200: {resp.text}"

    items = resp.json()["items"]

    with allure.step("items не пустой"):
        assert len(items) > 0, f"Ожидались события до {end}"

    with allure.step("Все items имеют createdAt < dateRangeEnd"):
        after_end = [item for item in items if item["createdAt"] >= "2026-08-15T00:00:00"]
        assert len(after_end) == 0, (
            f"{len(after_end)} событий после dateRangeEnd: "
            f"{[item['createdAt'] for item in after_end[:5]]}"
        )
