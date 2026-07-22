import allure
import time

from test_backend.data.endpoints.History.get_history_endpoint import get_history_endpoint
from test_backend.data.endpoints.History.assert_history_payload import assert_history_payload
from core.response_utils import short_resp

def assert_history_event_exists(
        client, space_id: str, kind: str, kind_id: str, expected_event_key: str,
        expected_data: dict = None, timeout: int = 20, interval: float = 1.0
) -> dict:
    """
    Вспомогательная функция: запрашивает историю с механизмом ожидания (поллингом).
    Если передан expected_data, функция будет искать событие, в котором data содержит указанные пары ключ-значение.
    """
    with allure.step(f"Ожидание события '{expected_event_key}' в истории {kind}"):
        start_time = time.time()
        found_event = None

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

            # Ищем подходящее событие
            for event in histories:
                if event.get('key') == expected_event_key:
                    # Если ожидаем конкретные данные, проверяем их
                    if expected_data:
                        event_data = event.get('data', {})
                        # Проверяем, что все ключи из expected_data есть в event_data и их значения совпадают
                        match = all(event_data.get(k) == v for k, v in expected_data.items())
                        if match:
                            found_event = event
                            break
                    else:
                        found_event = event
                        break

            if found_event:
                break

            time.sleep(interval)

        assert found_event is not None, (
            f"Событие {expected_event_key} с данными {expected_data} не найдено за {timeout} секунд. "
            f"Последний ответ: {histories}"
        )

        assert_history_payload(history=found_event, expected_kind=kind, expected_kind_id=kind_id)

        return found_event


def assert_history_event_not_exists(
        client, space_id: str, kind: str, kind_id: str, expected_event_key: str,
        expected_data: dict = None, after_ts: float = None, wait: float = 5.0
):
    """
    Проверяет, что событие НЕ появилось в истории.
    after_ts — timestamp (time.time()), после которого событие не должно было появиться.
    wait — сколько секунд подождать перед проверкой (дать бэкенду время на запись).
    """
    time.sleep(wait)

    with allure.step(f"Проверяем, что событие '{expected_event_key}' НЕ появилось"):
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
            if event.get('key') != expected_event_key:
                continue
            if expected_data:
                event_data = event.get('data', {})
                if not all(event_data.get(k) == v for k, v in expected_data.items()):
                    continue
            # Нашли совпадающее событие — если задан after_ts, проверяем время
            if after_ts:
                from datetime import datetime
                event_time = event.get('createdAt', '')
                # createdAt в ISO формате, парсим
                try:
                    event_dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                    if event_dt.timestamp() > after_ts:
                        raise AssertionError(
                            f"Событие {expected_event_key} с данными {expected_data} "
                            f"найдено после {after_ts}: {event}"
                        )
                except (ValueError, AttributeError):
                    pass
            else:
                raise AssertionError(
                    f"Событие {expected_event_key} с данными {expected_data} "
                    f"найдено, хотя не должно было появиться: {event}"
                )