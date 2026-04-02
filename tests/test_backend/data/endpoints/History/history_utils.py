import allure
import time

from test_backend.data.endpoints.History.get_history_endpoint import get_history_endpoint
from tests.test_backend.data.endpoints.History.assert_history_payload import assert_history_payload


def assert_history_event_exists(
        client, space_id: str, kind: str, kind_id: str, expected_event_key: str, timeout: int = 15, interval: float = 0.5
) -> dict:
    """
    Вспомогательная функция: запрашивает историю с механизмом ожидания (поллингом).
    Если событие не появилось сразу (т.к. история пишется асинхронно), функция будет
    повторять запросы до истечения timeout.
    """
    with allure.step(f"Ожидание события '{expected_event_key}' в истории {kind}"):
        start_time = time.time()
        event_keys = []
        histories = []

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
            event_keys = [event.get('key') for event in histories]

            if expected_event_key in event_keys:
                # Событие найдено, выходим из цикла
                break

            # Если не найдено, немного ждем перед следующим запросом
            time.sleep(interval)

        # Проверяем финальный результат после цикла
        assert expected_event_key in event_keys, (
            f"Событие {expected_event_key} не появилось в истории для {kind} с ID {kind_id} за {timeout} секунд. "
            f"Фактические события: {event_keys}"
        )

        # Находим и возвращаем сам объект события
        event = next(e for e in histories if e.get('key') == expected_event_key)

        # Валидируем базовую структуру найденного ивента
        assert_history_payload(history=event, expected_kind=kind, expected_kind_id=kind_id)

        return event