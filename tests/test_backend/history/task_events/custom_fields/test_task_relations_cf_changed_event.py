import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import (
    edit_task_custom_field_endpoint,
    delete_task_endpoint,
)
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


# ── Set / Change / Clear ──────────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@pytest.mark.parametrize("kind",
    ["Task", "Project", "Space"],
    ids=["Task", "Project", "Space"])
def test_task_relations_cf_set_event(main_client, space_for_history, project_for_history, temp_task, task_relations_custom_field, linked_tasks, kind):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при добавлении связанной задачи.
    Проверяем через GetHistory с kind=Task, kind=Project и kind=Space.
    Значение — массив из одного task ID.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = task_relations_custom_field["field_id"]
    field_name = task_relations_custom_field["field_name"]
    linked_id = linked_tasks[0]["task_id"]
    linked_name = linked_tasks[0]["name"]

    if kind == "Task":
        kind_id = task_id
    elif kind == "Project":
        kind_id = project_for_history["project_id"]
    else:
        kind_id = space_id

    allure.dynamic.title(f"[TaskRelations] добавление связанной задачи (GetHistory kind={kind})")

    with allure.step(f"Привязываем задачу '{linked_name}' к полю '{field_name}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[linked_id],
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
        assert data["fieldType"] == "TaskRelations", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("valueText непустой, isCleared = False"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert isinstance(data.get("valueText"), str) and data["valueText"], \
            f"valueText должен быть непустой строкой, получено: {data.get('valueText')!r}"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[TaskRelations] замена связанной задачи (GetHistory kind=Task)")
def test_task_relations_cf_change_event(main_client, space_for_history, temp_task, task_relations_custom_field, linked_tasks):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при замене связанной задачи.
    Привязываем задачу A, затем меняем на задачу B.
    Оба события имеют isCleared=False, используем min_count=2.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = task_relations_custom_field["field_id"]
    linked_a = linked_tasks[0]
    linked_b = linked_tasks[1]

    with allure.step(f"Привязываем задачу '{linked_a['name']}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[linked_a["task_id"]],
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

    with allure.step(f"Меняем на задачу '{linked_b['name']}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[linked_b["task_id"]],
        ))
        assert resp.status_code == 200, f"Ошибка при замене: {resp.text}"

    with allure.step("Проверяем событие замены (min_count=2)"):
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

    with allure.step("valueText содержит новую задачу, oldValueText — предыдущую"):
        assert isinstance(data.get("valueText"), str) and data["valueText"], \
            f"valueText должен быть непустой строкой: {data.get('valueText')!r}"
        assert isinstance(data.get("oldValueText"), str) and data["oldValueText"], \
            f"oldValueText должен быть непустой строкой: {data.get('oldValueText')!r}"
        assert data["isCleared"] is False


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[TaskRelations] удаление связанной задачи (GetHistory kind=Task)")
def test_task_relations_cf_clear_event(main_client, space_for_history, temp_task, task_relations_custom_field, linked_tasks):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при удалении связи.
    Привязываем задачу, затем очищаем (value=[]).
    Событие содержит isCleared=True и oldValueText.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = task_relations_custom_field["field_id"]
    field_name = task_relations_custom_field["field_name"]
    linked_id = linked_tasks[0]["task_id"]
    linked_name = linked_tasks[0]["name"]

    with allure.step(f"Привязываем задачу '{linked_name}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[linked_id],
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

    with allure.step("Удаляем связь (value=[])"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[],
        ))
        assert resp.status_code == 200, f"Ошибка при очистке: {resp.text}"

    with allure.step("Проверяем событие удаления связи (isCleared=True)"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": True},
        )

    data = event["data"]

    with allure.step("isCleared=True, oldValueText непустой"):
        assert data["isCleared"] is True, f"isCleared должен быть True: {data['isCleared']}"
        assert isinstance(data.get("oldValueText"), str) and data["oldValueText"], \
            f"oldValueText должен быть непустой строкой: {data.get('oldValueText')!r}"

    with allure.step("Метаданные поля: fieldName и fieldType сохранены"):
        assert data["fieldName"] == field_name, f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "TaskRelations", f"Неверный fieldType: {data['fieldType']}"


# ── Событие после удаления связанной задачи ───────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[TaskRelations] событие сохраняется после удаления связанной задачи")
def test_task_relations_cf_event_persists_after_deletion(main_client, space_for_history, temp_task, task_relations_custom_field, linked_tasks):
    """
    Проверяем что событие CUSTOM_FIELD_CHANGED остаётся в истории
    после удаления связанной задачи. Данные события не должны измениться.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = task_relations_custom_field["field_id"]
    linked_id = linked_tasks[0]["task_id"]
    linked_name = linked_tasks[0]["name"]

    with allure.step(f"Привязываем задачу '{linked_name}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[linked_id],
        ))
        assert resp.status_code == 200, f"Ошибка при установке: {resp.text}"

    with allure.step("Ожидаем событие (isCleared=False) и сохраняем valueText"):
        event_before = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )
        value_text_before = event_before["data"]["valueText"]

    with allure.step(f"Удаляем связанную задачу '{linked_name}'"):
        resp = main_client.post(**delete_task_endpoint(
            space_id=space_id, task_id=linked_id,
        ))
        assert resp.status_code == 200, f"Ошибка при удалении задачи: {resp.text}"

    with allure.step("Проверяем что событие осталось в истории с теми же данными"):
        event_after = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    data = event_after["data"]

    with allure.step(f"valueText не изменился: '{value_text_before}'"):
        assert data["valueText"] == value_text_before, \
            f"valueText изменился после удаления! Было: '{value_text_before}', стало: '{data['valueText']}'"
        assert data["fieldType"] == "TaskRelations"
        assert data["isCleared"] is False
