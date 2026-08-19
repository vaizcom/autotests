import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@pytest.mark.parametrize("kind",
    ["Task", "Project", "Space"],
    ids=["Task", "Project", "Space"])
def test_boolean_cf_toggle_on_event(main_client, space_for_history, project_for_history, temp_task, boolean_custom_field, kind):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при переключении Checkbox поля Off → On.
    Проверяем через GetHistory с kind=Task, kind=Project и kind=Space.
    API тип поля "Checkbox" (в UI — Boolean). По умолчанию Off.
    При установке value=True переключается в On. В valueText приходит "On".
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = boolean_custom_field["field_id"]
    field_name = boolean_custom_field["field_name"]

    if kind == "Task":
        kind_id = task_id
    elif kind == "Project":
        kind_id = project_for_history["project_id"]
    else:
        kind_id = space_id

    allure.dynamic.title(f"[Boolean] переключение Off → On (GetHistory kind={kind})")

    with allure.step(f"Переключаем Boolean поле '{field_name}' в On (value=True)"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=True,
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
        assert data["fieldType"] == "Checkbox", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("Значения: valueText = 'On', isCleared = False"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data["valueText"] == "On", \
            f"Неверный valueText. Ожидалось: 'On', получено: '{data.get('valueText')}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Boolean] переключение On → Off (GetHistory kind=Task)")
def test_boolean_cf_toggle_off_event(main_client, space_for_history, temp_task, boolean_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при переключении Checkbox поля On → Off.
    Проверяем через GetHistory с kind=Task.
    API тип поля "Checkbox" (в UI — Boolean).
    Устанавливаем True (On), затем False (Off) — событие должно содержать
    valueText = "Off" и oldValueText = "On".
    Оба события имеют isCleared=False, поэтому используем min_count=2.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = boolean_custom_field["field_id"]
    field_name = boolean_custom_field["field_name"]

    with allure.step("Переключаем Boolean поле в On (value=True)"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=True,
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие переключения Off → On (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Переключаем Boolean поле в Off (value=False)"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=False,
        ))
        assert resp.status_code == 200, f"Ошибка при переключении кастомного поля: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED: On → Off (min_count=2)"):
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
        assert data["fieldName"] == field_name, f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Checkbox", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("valueText = 'Off', oldValueText = 'On', isCleared = False"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data["valueText"] == "Off", \
            f"Неверный valueText. Ожидалось: 'Off', получено: '{data.get('valueText')}'"
        assert data["oldValueText"] == "On", \
            f"Неверный oldValueText. Ожидалось: 'On', получено: '{data.get('oldValueText')}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"
