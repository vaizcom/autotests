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
def test_estimation_cf_set_event(main_client, space_for_history, project_for_history, temp_task, estimation_custom_field, kind):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при установке Estimation поля.
    Проверяем через GetHistory с kind=Task, kind=Project и kind=Space.
    Значение передаётся в формате ISO 8601 Duration ("P1W2DT3H").
    В valueText приходит человекочитаемый формат ("1w 2d 3h").
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = estimation_custom_field["field_id"]
    field_name = estimation_custom_field["field_name"]
    new_value = "P1W2DT3H"
    expected_text = "1w 2d 3h"

    if kind == "Task":
        kind_id = task_id
    elif kind == "Project":
        kind_id = project_for_history["project_id"]
    else:
        kind_id = space_id

    allure.dynamic.title(f"[Estimation] установка значения (GetHistory kind={kind})")

    with allure.step(f"Устанавливаем Estimation '{field_name}' = {new_value}"):
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
        assert data["fieldType"] == "Estimation", f"Неверный fieldType: {data['fieldType']}"

    with allure.step(f"valueText = '{expected_text}', isCleared = False"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data["valueText"] == expected_text, \
            f"Неверный valueText. Ожидалось: '{expected_text}', получено: '{data.get('valueText')}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events")
@allure.title("[Estimation] изменение значения (GetHistory kind=Task)")
def test_estimation_cf_change_event(main_client, space_for_history, temp_task, estimation_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при изменении Estimation поля.
    Проверяем через GetHistory с kind=Task.
    Устанавливаем P1W, затем меняем на PT5H30M — событие должно содержать
    valueText с новым значением и oldValueText с предыдущим.
    Оба события имеют isCleared=False, поэтому используем min_count=2.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = estimation_custom_field["field_id"]
    field_name = estimation_custom_field["field_name"]
    initial_value = "P1W"
    updated_value = "PT5H30M"
    expected_old = "1w"
    expected_new = "5h 30m"

    with allure.step(f"Устанавливаем начальное значение Estimation = {initial_value}"):
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

    with allure.step(f"Меняем значение на {updated_value}"):
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
        assert data["fieldName"] == field_name, f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Estimation", f"Неверный fieldType: {data['fieldType']}"

    with allure.step(f"valueText = '{expected_new}', oldValueText = '{expected_old}'"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data["valueText"] == expected_new, \
            f"Неверный valueText. Ожидалось: '{expected_new}', получено: '{data.get('valueText')}'"
        assert data["oldValueText"] == expected_old, \
            f"Неверный oldValueText. Ожидалось: '{expected_old}', получено: '{data.get('oldValueText')}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events")
@allure.title("[Estimation] очистка значения (GetHistory kind=Task)")
def test_estimation_cf_clear_event(main_client, space_for_history, temp_task, estimation_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при очистке Estimation поля.
    Проверяем через GetHistory с kind=Task.
    Устанавливаем значение, затем очищаем (value="").
    Событие должно содержать isCleared=True и oldValueText с предыдущим значением.
    Примечание: через API очистка работает корректно (200, isCleared=true).
    На фронте есть баг — поле не очищается визуально.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = estimation_custom_field["field_id"]
    field_name = estimation_custom_field["field_name"]
    initial_value = "P3DT4H"
    expected_old = "3d 4h"

    with allure.step(f"Устанавливаем значение Estimation = {initial_value}"):
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

    with allure.step("Очищаем значение поля (пустая строка)"):
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
        assert data["fieldType"] == "Estimation", f"Неверный fieldType: {data['fieldType']}"

    with allure.step(f"isCleared=True, oldValueText = '{expected_old}'"):
        assert data["isCleared"] is True, f"isCleared должен быть True: {data['isCleared']}"
        assert data["oldValueText"] == expected_old, \
            f"Неверный oldValueText. Ожидалось: '{expected_old}', получено: '{data.get('oldValueText')}'"
