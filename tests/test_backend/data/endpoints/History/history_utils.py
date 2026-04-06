import allure
import time

from test_backend.data.endpoints.History.get_history_endpoint import get_history_endpoint
from tests.test_backend.data.endpoints.History.assert_history_payload import assert_history_payload

def assert_history_event_exists(
        client, space_id: str, kind: str, kind_id: str, expected_event_key: str,
        expected_data: dict = None, timeout: int = 20, interval: float = 0.5
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
                    limit=50
                )
            )
            assert resp.status_code == 200, f"Ошибка при получении истории: {resp.text}"

            histories = resp.json().get('payload', {}).get('histories', [])

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