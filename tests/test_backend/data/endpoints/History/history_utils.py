import time
from typing import Optional

from test_backend.data.endpoints.History.get_history_endpoint import get_history_endpoint
from core.response_utils import short_resp


def _find_event(histories: list, event_key: str, expected_data: dict = None) -> Optional[dict]:
    """Возвращает первое событие подходящее по key и data, или None."""
    for event in histories:
        if event.get('key') != event_key:
            continue
        if expected_data:
            data = event.get('data', {})
            if not all(data.get(k) == v for k, v in expected_data.items()):
                continue
        return event
    return None


def assert_get_history_event(
        client, space_id: str, kind: str, kind_id: str, expected_event_key: str,
        expected_data: dict = None, timeout: int = 30, interval: float = 1.0,
) -> dict:
    """
    Поллит GetHistory до появления нужного события.
    Возвращает найденное событие для дальнейших проверок в тесте.
    """
    deadline = time.monotonic() + timeout
    histories = []

    while time.monotonic() < deadline:
        resp = client.post(
            **get_history_endpoint(space_id=space_id, kind=kind, kind_id=kind_id, next_cursor=0)
        )
        assert resp.status_code == 200, f"GET /GetHistory вернул {resp.status_code}: {short_resp(resp)}"

        histories = resp.json().get('payload', {}).get('items', [])
        event = _find_event(histories, expected_event_key, expected_data)
        if event:
            return event

        time.sleep(interval)

    received_keys = [e.get('key') for e in histories]
    raise AssertionError(
        f"Событие '{expected_event_key}' не найдено за {timeout}с.\n"
        f"expected_data: {expected_data}\n"
        f"Получены события: {received_keys}"
    )


def assert_history_event_count(
        client, space_id: str, kind: str, kind_id: str, event_key: str, expected_count: int = 1,
):
    """
    Проверяет точное количество событий с данным key в истории.
    Вызывать после assert_get_history_event — событие уже гарантированно есть,
    поэтому один запрос без поллинга достаточен.
    """
    resp = client.post(
        **get_history_endpoint(space_id=space_id, kind=kind, kind_id=kind_id, next_cursor=0)
    )
    assert resp.status_code == 200, f"GET /GetHistory вернул {resp.status_code}: {short_resp(resp)}"

    items = resp.json().get('payload', {}).get('items', [])
    actual = sum(1 for e in items if e.get('key') == event_key)

    assert actual == expected_count, (
        f"Ожидалось {expected_count} событие(й) '{event_key}', получено {actual}"
    )


def assert_get_history_no_event(
        client, space_id: str, kind: str, kind_id: str, expected_event_key: str,
        expected_data: dict = None, wait: float = 5.0,
):
    """
    Проверяет что событие НЕ появилось в истории.
    wait — сколько секунд подождать перед проверкой (дать бэкенду время на запись).
    """
    time.sleep(wait)

    resp = client.post(
        **get_history_endpoint(space_id=space_id, kind=kind, kind_id=kind_id, next_cursor=0)
    )
    assert resp.status_code == 200, f"GET /GetHistory вернул {resp.status_code}: {short_resp(resp)}"

    histories = resp.json().get('payload', {}).get('items', [])
    event = _find_event(histories, expected_event_key, expected_data)

    assert event is None, (
        f"Событие '{expected_event_key}' найдено, хотя не должно было появиться.\n"
        f"expected_data: {expected_data}\n"
        f"Найденное событие: {event}"
    )
