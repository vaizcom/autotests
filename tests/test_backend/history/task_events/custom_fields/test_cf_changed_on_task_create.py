import time

import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import (
    edit_task_custom_field_endpoint,
    duplicate_task_endpoint,
)
from test_backend.data.endpoints.History.history_utils import (
    assert_get_history_event,
    assert_get_history_no_event,
    assert_history_event_count,
)

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[General] создание задачи без CF не генерирует CUSTOM_FIELD_CHANGED")
def test_task_create_no_cf_changed_events(main_client, space_for_history, temp_task, text_custom_field):
    """
    Проверяем что создание задачи без заполнения кастомных полей
    не генерирует событий CUSTOM_FIELD_CHANGED.
    CF-поле существует на борде, но значение не задано.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = text_custom_field["field_id"]

    with allure.step("Проверяем что для новой задачи нет событий CUSTOM_FIELD_CHANGED"):
        assert_get_history_no_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
        )


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[General] дублирование задачи с CF не дублирует CUSTOM_FIELD_CHANGED")
def test_duplicate_task_no_cf_changed_events(main_client, space_for_history, board_for_history, temp_task, text_custom_field):
    """
    Проверяем что при дублировании задачи с заполненным кастомным полем
    в истории дубля НЕ появляется CUSTOM_FIELD_CHANGED.
    Значения CF копируются, но это не отдельное действие пользователя.
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    task_id = temp_task
    field_id = text_custom_field["field_id"]

    with allure.step("Устанавливаем значение Text CF на оригинальной задаче"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value="original value",
        ))
        assert resp.status_code == 200, f"Ошибка при установке CF: {resp.text}"

    with allure.step("Ожидаем CUSTOM_FIELD_CHANGED на оригинальной задаче"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Дублируем задачу"):
        resp = main_client.post(**duplicate_task_endpoint(
            space_id=space_id, task_id=task_id, board_id=board_id,
        ))
        assert resp.status_code == 200, f"Ошибка при дублировании: {resp.text}"
        dup_task_id = resp.json()["payload"]["task"]["_id"]

    with allure.step("Проверяем что у дубля нет CUSTOM_FIELD_CHANGED событий"):
        assert_get_history_no_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=dup_task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
        )


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[General] два Text CF на одной борде — события различимы по fieldId/fieldName")
def test_multiple_same_type_cf_distinguishable(
    main_client, space_for_history, temp_task, text_custom_field, text_custom_field_2,
):
    """
    Редактируем два Text CF на одной задаче.
    Проверяем что в истории два разных CUSTOM_FIELD_CHANGED
    с разными fieldId, fieldName и valueText.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_1 = text_custom_field
    field_2 = text_custom_field_2

    with allure.step(f"Устанавливаем значение первого CF '{field_1['field_name']}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id,
            field_id=field_1["field_id"], value="value from field 1",
        ))
        assert resp.status_code == 200, f"Ошибка при установке CF-1: {resp.text}"

    with allure.step("Ожидаем событие для первого CF"):
        event_1 = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_1["field_id"], "isCleared": False},
        )

    with allure.step(f"Устанавливаем значение второго CF '{field_2['field_name']}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id,
            field_id=field_2["field_id"], value="value from field 2",
        ))
        assert resp.status_code == 200, f"Ошибка при установке CF-2: {resp.text}"

    with allure.step("Ожидаем событие для второго CF"):
        event_2 = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_2["field_id"], "isCleared": False},
        )

    with allure.step("fieldId и fieldName различаются между событиями"):
        assert event_1["data"]["fieldId"] != event_2["data"]["fieldId"], \
            "fieldId должны различаться"
        assert event_1["data"]["fieldName"] != event_2["data"]["fieldName"], \
            "fieldName должны различаться"

    with allure.step("valueText соответствуют своим полям"):
        assert event_1["data"]["valueText"] == "value from field 1", \
            f"Неверный valueText CF-1: {event_1['data']['valueText']}"
        assert event_2["data"]["valueText"] == "value from field 2", \
            f"Неверный valueText CF-2: {event_2['data']['valueText']}"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[General] повторная установка того же значения не создаёт дубль события")
def test_cf_changed_no_duplicate_on_same_value(
    main_client, space_for_history, temp_task, text_custom_field,
):
    """
    Устанавливаем Text CF = "idempotent value", ждём события.
    Затем устанавливаем то же значение повторно.
    Проверяем что второе событие НЕ появилось — количество CUSTOM_FIELD_CHANGED = 1.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = text_custom_field["field_id"]
    value = "idempotent value"

    with allure.step(f"Устанавливаем Text CF = '{value}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке CF: {resp.text}"

    with allure.step("Ожидаем событие CUSTOM_FIELD_CHANGED"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step(f"Повторно устанавливаем то же значение '{value}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=value,
        ))
        assert resp.status_code == 200, f"Ошибка при повторной установке CF: {resp.text}"

    with allure.step("Ждём 5 секунд и проверяем что событие не задублировалось"):
        time.sleep(5)
        assert_history_event_count(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            event_key="CUSTOM_FIELD_CHANGED",
            expected_count=1,
        )
