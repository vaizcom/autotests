import time

from test_backend.data.endpoints.History.get_history_endpoint import get_history_endpoint
from core.response_utils import short_resp


def _match_event(event: dict, expected_event_key: str, expected_data: dict = None) -> bool:
    """Проверяет, совпадает ли событие по key и (опционально) по data."""
    if event.get('key') != expected_event_key:
        return False
    if expected_data:
        event_data = event.get('data', {})
        return all(event_data.get(k) == v for k, v in expected_data.items())
    return True


def assert_get_history_event(
        client, space_id: str, kind: str, kind_id: str, expected_event_key: str,
        expected_data: dict = None, timeout: int = 20, interval: float = 1.0,
        assert_unique: bool = False,
) -> dict:
    """
    Поллит GetHistory до появления нужного события.

    Возвращает найденное событие (dict) для дальнейших проверок в тесте.
    Если assert_unique=True, проверяет что событие встречается ровно 1 раз.
    """
    start_time = time.time()
    found_event = None
    histories = []

    while time.time() - start_time < timeout:
        resp = client.post(
            **get_history_endpoint(
                space_id=space_id,
                kind=kind,
                kind_id=kind_id,
                next_cursor=0,
            )
        )
        assert resp.status_code == 200, f"Ошибка при получении истории: {short_resp(resp)}"

        histories = resp.json().get('payload', {}).get('items', [])

        for event in histories:
            if _match_event(event, expected_event_key, expected_data):
                found_event = event
                break

        if found_event:
            break

        time.sleep(interval)

    assert found_event is not None, (
        f"Событие {expected_event_key} с данными {expected_data} не найдено за {timeout} секунд. "
        f"Последний ответ: {histories}"
    )

    if assert_unique:
        duplicates = [e for e in histories if _match_event(e, expected_event_key, expected_data)]
        assert len(duplicates) == 1, (
            f"Событие {expected_event_key} найдено {len(duplicates)} раз (ожидалось 1). "
            f"IDs: {[e.get('_id') for e in duplicates]}"
        )

    return found_event


def assert_get_history_no_event(
        client, space_id: str, kind: str, kind_id: str, expected_event_key: str,
        expected_data: dict = None, wait: float = 5.0,
):
    """
    Проверяет, что событие НЕ появилось в истории.
    wait — сколько секунд подождать перед проверкой (дать бэкенду время на запись).
    """
    time.sleep(wait)

    resp = client.post(
        **get_history_endpoint(
            space_id=space_id,
            kind=kind,
            kind_id=kind_id,
            next_cursor=0,
        )
    )
    assert resp.status_code == 200, f"Ошибка при получении истории: {short_resp(resp)}"

    histories = resp.json().get('payload', {}).get('items', [])

    for event in histories:
        if _match_event(event, expected_event_key, expected_data):
            assert False, (
                f"Событие {expected_event_key} с данными {expected_data} "
                f"найдено, хотя не должно было появиться: {event}"
            )