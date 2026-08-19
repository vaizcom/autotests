import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint
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
def test_url_cf_set_event(main_client, space_for_history, project_for_history, temp_task, url_custom_field, kind):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при добавлении ссылки в Url поле.
    Проверяем через GetHistory с kind=Task, kind=Project и kind=Space.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = url_custom_field["field_id"]
    field_name = url_custom_field["field_name"]
    url_value = "https://example.com"

    if kind == "Task":
        kind_id = task_id
    elif kind == "Project":
        kind_id = project_for_history["project_id"]
    else:
        kind_id = space_id

    allure.dynamic.title(f"[Url] добавление ссылки (GetHistory kind={kind})")

    with allure.step(f"Устанавливаем Url поле '{field_name}' = '{url_value}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=url_value,
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
        assert data["fieldType"] == "Url", f"Неверный fieldType: {data['fieldType']}"

    with allure.step(f"valueText = '{url_value}', isCleared = False"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data["valueText"] == url_value, \
            f"Неверный valueText. Ожидалось: '{url_value}', получено: '{data.get('valueText')}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Url] изменение ссылки (GetHistory kind=Task)")
def test_url_cf_change_event(main_client, space_for_history, temp_task, url_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при изменении ссылки.
    Устанавливаем первую ссылку, затем меняем на другую.
    Оба события имеют isCleared=False, поэтому используем min_count=2.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = url_custom_field["field_id"]
    url_first = "https://example.com/first"
    url_second = "https://example.com/second"

    with allure.step(f"Устанавливаем первую ссылку '{url_first}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=url_first,
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

    with allure.step(f"Меняем ссылку на '{url_second}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=url_second,
        ))
        assert resp.status_code == 200, f"Ошибка при изменении ссылки: {resp.text}"

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

    with allure.step(f"valueText = '{url_second}', oldValueText = '{url_first}'"):
        assert data["valueText"] == url_second, \
            f"Неверный valueText. Ожидалось: '{url_second}', получено: '{data.get('valueText')}'"
        assert data["oldValueText"] == url_first, \
            f"Неверный oldValueText. Ожидалось: '{url_first}', получено: '{data.get('oldValueText')}'"
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Url] удаление ссылки (GetHistory kind=Task)")
def test_url_cf_clear_event(main_client, space_for_history, temp_task, url_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при удалении ссылки.
    Устанавливаем значение, затем очищаем (value="").
    Событие содержит isCleared=True и oldValueText с предыдущей ссылкой.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = url_custom_field["field_id"]
    field_name = url_custom_field["field_name"]
    url_value = "https://example.com/to-clear"

    with allure.step(f"Устанавливаем ссылку '{url_value}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=url_value,
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

    with allure.step("Удаляем ссылку (value='')"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value="",
        ))
        assert resp.status_code == 200, f"Ошибка при очистке кастомного поля: {resp.text}"

    with allure.step("Проверяем событие удаления (isCleared=True)"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": True},
        )

    data = event["data"]

    with allure.step(f"isCleared=True, oldValueText = '{url_value}'"):
        assert data["isCleared"] is True, f"isCleared должен быть True: {data['isCleared']}"
        assert data["oldValueText"] == url_value, \
            f"Неверный oldValueText. Ожидалось: '{url_value}', получено: '{data.get('oldValueText')}'"

    with allure.step("Метаданные поля: fieldName и fieldType сохранены"):
        assert data["fieldName"] == field_name, f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Url", f"Неверный fieldType: {data['fieldType']}"


# ── Спецсимволы / query params ────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Url] ссылка с query params и спецсимволами (GetHistory kind=Task)")
def test_url_cf_special_chars_event(main_client, space_for_history, temp_task, url_custom_field):
    """
    Проверяем что ссылка с query params, фрагментом и спецсимволами
    корректно сохраняется в valueText без обрезки и экранирования.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = url_custom_field["field_id"]
    url_value = "https://example.com/path?foo=bar&baz=1#section-2"

    with allure.step(f"Устанавливаем ссылку со спецсимволами: '{url_value}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=url_value,
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED"):
        event = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    data = event["data"]

    with allure.step("valueText содержит полную ссылку с query params и фрагментом"):
        assert data["valueText"] == url_value, \
            f"valueText не совпадает. Ожидалось: '{url_value}', получено: '{data.get('valueText')}'"
