import uuid

import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events")
@pytest.mark.parametrize("kind",
    ["Task", "Project", "Space"],
    ids=["Task", "Project", "Space"])
def test_custom_field_set_event(main_client, space_for_history, project_for_history, temp_task, text_custom_field, kind):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при установке значения Text кастомного поля.
    Проверяем через GetHistory с kind=Task, kind=Project и kind=Space.
    Событие должно содержать метаданные поля (fieldId, fieldName, fieldType),
    новое значение (valueText) и флаг isCleared=False.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = text_custom_field["field_id"]
    field_name = text_custom_field["field_name"]
    new_value = f"autotest-{uuid.uuid4().hex[:8]}"

    if kind == "Task":
        kind_id = task_id
    elif kind == "Project":
        kind_id = project_for_history["project_id"]
    else:
        kind_id = space_id

    allure.dynamic.title(f"[Text] установка значения (GetHistory kind={kind})")

    with allure.step(f"Устанавливаем значение Text поля '{field_name}' = '{new_value}'"):
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
        assert data["fieldType"] == "Text", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("Значения: valueText = новое значение, isCleared = False"):
        assert data["valueText"] == new_value, \
            f"Неверный valueText. Ожидалось: '{new_value}', получено: '{data['valueText']}'"
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events")
@allure.title("[Text] изменение значения (GetHistory kind=Task)")
def test_custom_field_change_event(main_client, space_for_history, temp_task, text_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при изменении значения Text поля.
    Устанавливаем первое значение, затем меняем на другое.
    Оба события имеют isCleared=False, поэтому используем min_count=2.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = text_custom_field["field_id"]
    first_value = f"autotest-{uuid.uuid4().hex[:8]}"
    second_value = f"autotest-{uuid.uuid4().hex[:8]}"

    with allure.step(f"Устанавливаем первое значение '{first_value}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=first_value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке: {resp.text}"

    with allure.step("Ожидаем событие установки (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step(f"Меняем значение на '{second_value}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=second_value,
        ))
        assert resp.status_code == 200, f"Ошибка при изменении: {resp.text}"

    with allure.step("Проверяем событие изменения (min_count=2)"):
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

    with allure.step(f"valueText = '{second_value}', oldValueText = '{first_value}'"):
        assert data["valueText"] == second_value, \
            f"Неверный valueText. Ожидалось: '{second_value}', получено: '{data.get('valueText')}'"
        assert data["oldValueText"] == first_value, \
            f"Неверный oldValueText. Ожидалось: '{first_value}', получено: '{data.get('oldValueText')}'"
        assert data["isCleared"] is False


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events")
@allure.title("[Text] спецсимволы и emoji (GetHistory kind=Task)")
def test_custom_field_special_chars_event(main_client, space_for_history, temp_task, text_custom_field):
    """
    Проверяем что спецсимволы, HTML-сущности и emoji корректно сохраняются
    в valueText без экранирования и обрезки.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = text_custom_field["field_id"]
    special_value = "<script>alert('xss')</script> & \"quotes\" 🚀✅"

    with allure.step(f"Устанавливаем значение со спецсимволами и emoji"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=special_value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("valueText содержит исходную строку без экранирования"):
        assert event["data"]["valueText"] == special_value, \
            f"valueText не совпадает. Ожидалось: {special_value!r}, получено: {event['data']['valueText']!r}"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events")
@allure.title("[Text] очистка значения (GetHistory kind=Task)")
def test_custom_field_clear_event(main_client, space_for_history, temp_task, text_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при очистке значения Text поля.
    После установки значения ожидаем записи события, затем очищаем поле и проверяем,
    что записалось новое событие с isCleared=True, а oldValueText содержит предыдущее значение.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = text_custom_field["field_id"]
    field_name = text_custom_field["field_name"]
    initial_value = f"autotest-{uuid.uuid4().hex[:8]}"

    with allure.step(f"Устанавливаем начальное значение Text поля = '{initial_value}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=initial_value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED: установка значения (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Очищаем значение поля (пустая строка)"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value="",
        ))
        assert resp.status_code == 200, f"Ошибка при очистке кастомного поля: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED: очистка значения (isCleared=True, oldValueText)"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": True},
        )

    data = event["data"]

    with allure.step("isCleared=True, oldValueText содержит предыдущее значение"):
        assert data["isCleared"] is True, f"isCleared должен быть True: {data['isCleared']}"
        assert data.get("oldValueText") == initial_value, \
            f"oldValueText должен быть '{initial_value}', получено: {data.get('oldValueText')}"

    with allure.step("Метаданные поля: fieldName и fieldType сохранены"):
        assert data["fieldName"] == field_name, f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Text", f"Неверный fieldType: {data['fieldType']}"
