from datetime import datetime, timedelta, timezone

import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


def _iso_date(days_ahead):
    """ISO 8601 дата с отступом от сегодня (UTC)."""
    dt = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    return dt.strftime("%Y-%m-%dT00:00:00.000Z")


def _expected_date_text(iso_str):
    """Конвертирует ISO-строку в ожидаемый формат valueText: 'Month DD, YYYY'."""
    dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.000Z")
    return dt.strftime("%B %d, %Y")


# ── Single Date ──────────────────────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@pytest.mark.parametrize("kind",
    ["Task", "Project", "Space"],
    ids=["Task", "Project", "Space"])
def test_date_cf_set_single_event(main_client, space_for_history, project_for_history, temp_task, date_custom_field, kind):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при установке одиночной даты (Single Date).
    Проверяем через GetHistory с kind=Task, kind=Project и kind=Space.
    API Date поля принимает массив [start, end]:
    - Single Date: [null, ISO-дата] — только конечная дата.
    - Date Range: [ISO-start, ISO-end] — обе даты заполнены.
    В valueText дата приходит в формате "Month DD, YYYY" (например, "August 23, 2026").
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = date_custom_field["field_id"]
    field_name = date_custom_field["field_name"]
    new_value = [None, _iso_date(days_ahead=5)]
    expected_date = _expected_date_text(new_value[1])

    if kind == "Task":
        kind_id = task_id
    elif kind == "Project":
        kind_id = project_for_history["project_id"]
    else:
        kind_id = space_id

    allure.dynamic.title(f"[Date] установка одиночной даты (GetHistory kind={kind})")

    with allure.step(f"Устанавливаем Single Date на поле '{field_name}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=new_value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step(f"Проверяем событие CUSTOM_FIELD_CHANGED через GetHistory kind={kind}"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind=kind,
            kind_id=kind_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    data = event["data"]

    with allure.step("Метаданные поля: fieldId, fieldName, fieldType корректны"):
        assert data["fieldId"] == field_id, f"Неверный fieldId: {data['fieldId']}"
        assert data["fieldName"] == field_name, f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Date", f"Неверный fieldType: {data['fieldType']}"

    with allure.step(f"valueText = '{expected_date}', isCleared = False"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data["valueText"] == expected_date, \
            f"Неверный valueText. Ожидалось: '{expected_date}', получено: '{data['valueText']}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Date] изменение одиночной даты (GetHistory kind=Task)")
def test_date_cf_change_single_event(main_client, space_for_history, temp_task, date_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при изменении одиночной даты.
    Проверяем через GetHistory с kind=Task.
    Устанавливаем дату, затем меняем на другую — событие должно содержать
    oldValueText с предыдущим значением и valueText с новым.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = date_custom_field["field_id"]
    initial_value = [None, _iso_date(days_ahead=3)]
    updated_value = [None, _iso_date(days_ahead=15)]
    expected_old = _expected_date_text(initial_value[1])
    expected_new = _expected_date_text(updated_value[1])

    with allure.step("Устанавливаем начальное значение Single Date"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=initial_value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие установки (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Меняем дату на другую"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=updated_value,
        ))
        assert resp.status_code == 200, f"Ошибка при изменении кастомного поля: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED: изменение значения (min_count=2)"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
            min_count=2,
        )

    data = event["data"]

    with allure.step("Метаданные поля: fieldId, fieldName, fieldType корректны"):
        assert data["fieldId"] == field_id, f"Неверный fieldId: {data['fieldId']}"
        assert data["fieldName"] == date_custom_field["field_name"], \
            f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Date", f"Неверный fieldType: {data['fieldType']}"

    with allure.step(f"isCleared = False, valueText = '{expected_new}'"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data["valueText"] == expected_new, \
            f"Неверный valueText. Ожидалось: '{expected_new}', получено: '{data['valueText']}'"

    with allure.step(f"oldValueText = '{expected_old}' (предыдущее значение)"):
        assert data["oldValueText"] == expected_old, \
            f"Неверный oldValueText. Ожидалось: '{expected_old}', получено: '{data['oldValueText']}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Date] очистка одиночной даты (GetHistory kind=Task)")
def test_date_cf_clear_single_event(main_client, space_for_history, temp_task, date_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при очистке одиночной даты.
    Проверяем через GetHistory с kind=Task.
    Очистка выполняется через value="" (также работает [None, None], но [] — ошибка валидации).
    После очистки событие должно содержать isCleared=True и oldValueText с предыдущим значением.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = date_custom_field["field_id"]
    field_name = date_custom_field["field_name"]
    initial_value = [None, _iso_date(days_ahead=7)]
    expected_old = _expected_date_text(initial_value[1])

    with allure.step("Устанавливаем начальное значение Single Date"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=initial_value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие установки (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Очищаем значение поля"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value="",
        ))
        assert resp.status_code == 200, f"Ошибка при очистке кастомного поля: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED: очистка (isCleared=True)"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": True},
        )

    data = event["data"]

    with allure.step("Метаданные поля: fieldId, fieldName, fieldType корректны"):
        assert data["fieldId"] == field_id, f"Неверный fieldId: {data['fieldId']}"
        assert data["fieldName"] == field_name, f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Date", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("isCleared = True, значение поля очищено"):
        assert data["isCleared"] is True, f"isCleared должен быть True: {data['isCleared']}"

    with allure.step(f"oldValueText = '{expected_old}' (предыдущее значение до очистки)"):
        assert data["oldValueText"] == expected_old, \
            f"Неверный oldValueText. Ожидалось: '{expected_old}', получено: '{data['oldValueText']}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


# ── Date Range ───────────────────────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Date] установка диапазона дат (GetHistory kind=Task)")
def test_date_cf_set_range_event(main_client, space_for_history, temp_task, date_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при установке диапазона дат (Date Range).
    Проверяем через GetHistory с kind=Task.
    Значение передаётся как массив [ISO-start, ISO-end].
    В valueText приходит в формате "Month DD, YYYY → Month DD, YYYY".
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = date_custom_field["field_id"]
    field_name = date_custom_field["field_name"]
    new_value = [_iso_date(days_ahead=10), _iso_date(days_ahead=20)]
    expected_start = _expected_date_text(new_value[0])
    expected_end = _expected_date_text(new_value[1])

    with allure.step(f"Устанавливаем Date Range на поле '{field_name}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=new_value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED через GetHistory kind=Task"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    data = event["data"]

    with allure.step("Метаданные поля: fieldId, fieldName, fieldType корректны"):
        assert data["fieldId"] == field_id, f"Неверный fieldId: {data['fieldId']}"
        assert data["fieldName"] == field_name, f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Date", f"Неверный fieldType: {data['fieldType']}"

    with allure.step(f"valueText содержит '{expected_start}' и '{expected_end}'"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        value_text = data["valueText"]
        assert expected_start in value_text, \
            f"valueText не содержит start-дату '{expected_start}': '{value_text}'"
        assert expected_end in value_text, \
            f"valueText не содержит end-дату '{expected_end}': '{value_text}'"
        assert "→" in value_text, f"valueText не содержит разделитель '→': '{value_text}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Date] изменение диапазона дат (GetHistory kind=Task)")
def test_date_cf_change_range_event(main_client, space_for_history, temp_task, date_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при изменении диапазона дат.
    Проверяем через GetHistory с kind=Task.
    Устанавливаем range, затем меняем на другой — событие должно содержать
    oldValueText с предыдущим значением и valueText с новым.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = date_custom_field["field_id"]
    initial_value = [_iso_date(days_ahead=2), _iso_date(days_ahead=8)]
    updated_value = [_iso_date(days_ahead=30), _iso_date(days_ahead=45)]
    expected_new_start = _expected_date_text(updated_value[0])
    expected_new_end = _expected_date_text(updated_value[1])
    expected_old_start = _expected_date_text(initial_value[0])

    with allure.step("Устанавливаем начальный Date Range"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=initial_value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие установки (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Меняем диапазон на другой"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=updated_value,
        ))
        assert resp.status_code == 200, f"Ошибка при изменении кастомного поля: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED: изменение диапазона (min_count=2)"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
            min_count=2,
        )

    data = event["data"]

    with allure.step("Метаданные поля: fieldId, fieldName, fieldType корректны"):
        assert data["fieldId"] == field_id, f"Неверный fieldId: {data['fieldId']}"
        assert data["fieldName"] == date_custom_field["field_name"], \
            f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Date", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("isCleared = False, значение изменено"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"

    with allure.step(f"valueText содержит новый диапазон: '{expected_new_start}' → '{expected_new_end}'"):
        assert expected_new_start in data["valueText"], \
            f"valueText не содержит новую start-дату: '{data['valueText']}'"
        assert expected_new_end in data["valueText"], \
            f"valueText не содержит новую end-дату: '{data['valueText']}'"
        assert "→" in data["valueText"], f"valueText не содержит разделитель '→': '{data['valueText']}'"

    with allure.step(f"oldValueText содержит предыдущий диапазон (start: '{expected_old_start}')"):
        assert expected_old_start in data["oldValueText"], \
            f"oldValueText не содержит предыдущую start-дату: '{data['oldValueText']}'"
        assert "→" in data["oldValueText"], \
            f"oldValueText не содержит разделитель '→': '{data['oldValueText']}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Date] очистка диапазона дат (GetHistory kind=Task)")
def test_date_cf_clear_range_event(main_client, space_for_history, temp_task, date_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при очистке диапазона дат.
    Проверяем через GetHistory с kind=Task.
    Очистка выполняется через value="" (также работает [None, None], но [] — ошибка валидации).
    После очистки событие должно содержать isCleared=True и oldValueText
    с предыдущим значением в формате range.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = date_custom_field["field_id"]
    field_name = date_custom_field["field_name"]
    initial_value = [_iso_date(days_ahead=5), _iso_date(days_ahead=12)]
    expected_old_start = _expected_date_text(initial_value[0])

    with allure.step("Устанавливаем Date Range"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=initial_value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие установки (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Очищаем значение поля"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value="",
        ))
        assert resp.status_code == 200, f"Ошибка при очистке кастомного поля: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED: очистка range (isCleared=True)"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": True},
        )

    data = event["data"]

    with allure.step("Метаданные поля: fieldId, fieldName, fieldType корректны"):
        assert data["fieldId"] == field_id, f"Неверный fieldId: {data['fieldId']}"
        assert data["fieldName"] == field_name, f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Date", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("isCleared = True, значение диапазона очищено"):
        assert data["isCleared"] is True, f"isCleared должен быть True: {data['isCleared']}"

    with allure.step(f"oldValueText содержит предыдущий диапазон (start: '{expected_old_start}')"):
        assert expected_old_start in data["oldValueText"], \
            f"oldValueText не содержит start-дату '{expected_old_start}': '{data['oldValueText']}'"
        assert "→" in data["oldValueText"], \
            f"oldValueText не содержит разделитель '→': '{data['oldValueText']}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"
