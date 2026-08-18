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
def test_member_cf_set_event(main_client, space_for_history, project_for_history, temp_task, member_custom_field, history_members, kind):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при назначении мембера в Member поле.
    Проверяем через GetHistory с kind=Task, kind=Project и kind=Space.
    Значение передаётся как массив member ID: [member_id].
    В valueText приходит fullName мембера, в memberIds — массив назначенных ID.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = member_custom_field["field_id"]
    field_name = member_custom_field["field_name"]
    member_id = history_members["main"][0]

    if kind == "Task":
        kind_id = task_id
    elif kind == "Project":
        kind_id = project_for_history["project_id"]
    else:
        kind_id = space_id

    allure.dynamic.title(f"[Member] назначение мембера (GetHistory kind={kind})")

    with allure.step(f"Назначаем мембера в поле '{field_name}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[member_id],
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
        assert data["fieldType"] == "Member", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("valueText содержит имя мембера, memberIds содержит назначенный ID"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data.get("valueText"), f"valueText должен быть непустым: {data.get('valueText')}"
        assert data.get("memberIds") == [member_id], \
            f"Неверный memberIds. Ожидалось: [{member_id}], получено: {data.get('memberIds')}"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events")
@allure.title("[Member] назначение нескольких мемберов (GetHistory kind=Task)")
def test_member_cf_set_multiple_event(main_client, space_for_history, temp_task, member_custom_field, history_members):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при назначении нескольких мемберов.
    Проверяем через GetHistory с kind=Task.
    Значение передаётся как массив из двух member ID: [main_id, manager_id].
    В memberIds приходит массив обоих ID, valueText содержит имена через запятую.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = member_custom_field["field_id"]
    field_name = member_custom_field["field_name"]
    main_id = history_members["main"][0]
    manager_id = history_members["manager"][0]
    members_value = [main_id, manager_id]

    with allure.step(f"Назначаем двух мемберов в поле '{field_name}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=members_value,
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
        assert data["fieldType"] == "Member", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("memberIds содержит оба ID, valueText непустой"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data.get("valueText"), f"valueText должен быть непустым: {data.get('valueText')}"
        actual_ids = sorted(data.get("memberIds", []))
        expected_ids = sorted(members_value)
        assert actual_ids == expected_ids, \
            f"Неверный memberIds. Ожидалось: {expected_ids}, получено: {actual_ids}"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events")
@allure.title("[Member] смена мембера (GetHistory kind=Task)")
def test_member_cf_change_event(main_client, space_for_history, temp_task, member_custom_field, history_members):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при смене мембера в Member поле.
    Проверяем через GetHistory с kind=Task.
    Назначаем main, затем меняем на manager — событие должно содержать
    valueText с именем нового мембера и oldValueText с именем предыдущего.
    Оба события имеют isCleared=False, поэтому используем min_count=2.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = member_custom_field["field_id"]
    field_name = member_custom_field["field_name"]
    main_id = history_members["main"][0]
    manager_id = history_members["manager"][0]

    with allure.step("Назначаем первого мембера (main)"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[main_id],
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие назначения (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Меняем мембера на manager"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[manager_id],
        ))
        assert resp.status_code == 200, f"Ошибка при смене мембера: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED: смена мембера (min_count=2)"):
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
        assert data["fieldType"] == "Member", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("valueText и oldValueText содержат имена мемберов, memberIds обновлён"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data.get("valueText"), f"valueText должен быть непустым: {data.get('valueText')}"
        assert data.get("oldValueText"), f"oldValueText должен быть непустым: {data.get('oldValueText')}"
        assert data.get("memberIds") == [manager_id], \
            f"Неверный memberIds. Ожидалось: [{manager_id}], получено: {data.get('memberIds')}"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events")
@allure.title("[Member] очистка мембера (GetHistory kind=Task)")
def test_member_cf_clear_event(main_client, space_for_history, temp_task, member_custom_field, history_members):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при очистке Member поля.
    Проверяем через GetHistory с kind=Task.
    Назначаем мембера, затем очищаем поле (value=[]).
    Событие должно содержать isCleared=True и oldValueText с именем предыдущего мембера.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = member_custom_field["field_id"]
    field_name = member_custom_field["field_name"]
    member_id = history_members["main"][0]

    with allure.step("Назначаем мембера"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[member_id],
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие назначения (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Очищаем Member поле (value=[])"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[],
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
        assert data["fieldType"] == "Member", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("isCleared=True, oldValueText содержит имя предыдущего мембера"):
        assert data["isCleared"] is True, f"isCleared должен быть True: {data['isCleared']}"
        assert data.get("oldValueText"), \
            f"oldValueText должен быть непустым: {data.get('oldValueText')}"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"
