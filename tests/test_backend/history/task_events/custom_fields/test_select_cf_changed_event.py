import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import edit_board_custom_field_endpoint
from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


# ── Single select ───────────────────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@pytest.mark.parametrize("kind",
    ["Task", "Project", "Space"],
    ids=["Task", "Project", "Space"])
def test_select_cf_set_single_event(main_client, space_for_history, project_for_history, temp_task, select_custom_field, kind):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при выборе одного option в Select поле.
    Проверяем через GetHistory с kind=Task, kind=Project и kind=Space.
    Значение передаётся как массив option ID: [opt_id].
    В valueText приходит title выбранной опции.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = select_custom_field["field_id"]
    field_name = select_custom_field["field_name"]
    opt_a = select_custom_field["opt_a"]

    if kind == "Task":
        kind_id = task_id
    elif kind == "Project":
        kind_id = project_for_history["project_id"]
    else:
        kind_id = space_id

    allure.dynamic.title(f"[Select] выбор одного значения (GetHistory kind={kind})")

    with allure.step(f"Выбираем опцию 'Alpha' в поле '{field_name}'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_a],
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
        assert data["fieldType"] == "Select", f"Неверный fieldType: {data['fieldType']}"

    with allure.step("valueText = 'Alpha' (название выбранной опции), isCleared = False"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data["valueText"] == "Alpha", \
            f"Неверный valueText. Ожидалось: 'Alpha', получено: '{data.get('valueText')}'"

    with allure.step("Контекст задачи: _id, name, hrid присутствуют"):
        assert data["_id"] == task_id, f"Неверный _id задачи: {data['_id']}"
        assert data["name"] == _TASK_NAME, f"Неверный name задачи: {data['name']}"
        assert isinstance(data.get("hrid"), str) and data["hrid"], "hrid должен быть непустой строкой"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Select] изменение одного option на другой (GetHistory kind=Task)")
def test_select_cf_change_single_event(main_client, space_for_history, temp_task, select_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при смене option в Select поле.
    Проверяем через GetHistory с kind=Task.
    Выбираем Alpha, затем меняем на Beta — событие содержит
    valueText = "Beta" и oldValueText = "Alpha".
    Оба события имеют isCleared=False, поэтому используем min_count=2.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = select_custom_field["field_id"]
    opt_a = select_custom_field["opt_a"]
    opt_b = select_custom_field["opt_b"]

    with allure.step("Выбираем опцию 'Alpha'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_a],
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие выбора (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Меняем на опцию 'Beta'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_b],
        ))
        assert resp.status_code == 200, f"Ошибка при смене опции: {resp.text}"

    with allure.step("Проверяем событие CUSTOM_FIELD_CHANGED: Alpha → Beta (min_count=2)"):
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

    with allure.step("valueText = 'Beta', oldValueText = 'Alpha'"):
        assert data["valueText"] == "Beta", \
            f"Неверный valueText. Ожидалось: 'Beta', получено: '{data.get('valueText')}'"
        assert data["oldValueText"] == "Alpha", \
            f"Неверный oldValueText. Ожидалось: 'Alpha', получено: '{data.get('oldValueText')}'"
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Select] очистка выбранного option (GetHistory kind=Task)")
def test_select_cf_clear_event(main_client, space_for_history, temp_task, select_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при очистке Select поля.
    Проверяем через GetHistory с kind=Task.
    Выбираем опцию, затем очищаем (value=[]).
    Событие содержит isCleared=True и oldValueText с названием предыдущей опции.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = select_custom_field["field_id"]
    field_name = select_custom_field["field_name"]
    opt_a = select_custom_field["opt_a"]

    with allure.step("Выбираем опцию 'Alpha'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_a],
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие выбора (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Очищаем Select поле (value=[])"):
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

    with allure.step("isCleared=True, oldValueText = 'Alpha'"):
        assert data["isCleared"] is True, f"isCleared должен быть True: {data['isCleared']}"
        assert data["oldValueText"] == "Alpha", \
            f"Неверный oldValueText. Ожидалось: 'Alpha', получено: '{data.get('oldValueText')}'"

    with allure.step("Метаданные поля: fieldName и fieldType сохранены"):
        assert data["fieldName"] == field_name, f"Неверный fieldName: {data['fieldName']}"
        assert data["fieldType"] == "Select", f"Неверный fieldType: {data['fieldType']}"


# ── Multi select ────────────────────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Select] выбор нескольких значений (GetHistory kind=Task)")
def test_select_cf_set_multiple_event(main_client, space_for_history, temp_task, select_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при выборе нескольких опций.
    Проверяем через GetHistory с kind=Task.
    Значение — массив из нескольких option ID.
    В valueText приходят названия опций через запятую: "Alpha, Beta, Gamma".
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = select_custom_field["field_id"]
    opt_a = select_custom_field["opt_a"]
    opt_b = select_custom_field["opt_b"]
    opt_c = select_custom_field["opt_c"]

    with allure.step("Выбираем три опции: Alpha, Beta, Gamma"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_a, opt_b, opt_c],
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

    with allure.step("valueText = 'Alpha, Beta, Gamma', isCleared = False"):
        assert data["isCleared"] is False, f"isCleared должен быть False: {data['isCleared']}"
        assert data["valueText"] == "Alpha, Beta, Gamma", \
            f"Неверный valueText. Ожидалось: 'Alpha, Beta, Gamma', получено: '{data.get('valueText')}'"

    with allure.step("Метаданные поля: fieldType = Select"):
        assert data["fieldType"] == "Select", f"Неверный fieldType: {data['fieldType']}"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Select] изменение одного значения на несколько (GetHistory kind=Task)")
def test_select_cf_single_to_multiple_event(main_client, space_for_history, temp_task, select_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при смене одного option на несколько.
    Проверяем через GetHistory с kind=Task.
    Выбираем Alpha, затем меняем на [Alpha, Beta] — событие содержит
    valueText = "Alpha, Beta" и oldValueText = "Alpha".
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = select_custom_field["field_id"]
    opt_a = select_custom_field["opt_a"]
    opt_b = select_custom_field["opt_b"]

    with allure.step("Выбираем одну опцию 'Alpha'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_a],
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие выбора (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Меняем на [Alpha, Beta]"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_a, opt_b],
        ))
        assert resp.status_code == 200, f"Ошибка при смене опций: {resp.text}"

    with allure.step("Проверяем событие: single → multiple (min_count=2)"):
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

    with allure.step("valueText = 'Alpha, Beta', oldValueText = 'Alpha'"):
        assert data["valueText"] == "Alpha, Beta", \
            f"Неверный valueText. Ожидалось: 'Alpha, Beta', получено: '{data.get('valueText')}'"
        assert data["oldValueText"] == "Alpha", \
            f"Неверный oldValueText. Ожидалось: 'Alpha', получено: '{data.get('oldValueText')}'"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Select] изменение нескольких значений на одно (GetHistory kind=Task)")
def test_select_cf_multiple_to_single_event(main_client, space_for_history, temp_task, select_custom_field):
    """
    Проверяем генерацию события CUSTOM_FIELD_CHANGED при смене нескольких опций на одну.
    Проверяем через GetHistory с kind=Task.
    Выбираем [Alpha, Beta, Gamma], затем меняем на [Gamma] — событие содержит
    valueText = "Gamma" и oldValueText = "Alpha, Beta, Gamma".
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = select_custom_field["field_id"]
    opt_a = select_custom_field["opt_a"]
    opt_b = select_custom_field["opt_b"]
    opt_c = select_custom_field["opt_c"]

    with allure.step("Выбираем три опции: Alpha, Beta, Gamma"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_a, opt_b, opt_c],
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие выбора (isCleared=False)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Меняем на одну опцию [Gamma]"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_c],
        ))
        assert resp.status_code == 200, f"Ошибка при смене опций: {resp.text}"

    with allure.step("Проверяем событие: multiple → single (min_count=2)"):
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

    with allure.step("valueText = 'Gamma', oldValueText = 'Alpha, Beta, Gamma'"):
        assert data["valueText"] == "Gamma", \
            f"Неверный valueText. Ожидалось: 'Gamma', получено: '{data.get('valueText')}'"
        assert data["oldValueText"] == "Alpha, Beta, Gamma", \
            f"Неверный oldValueText. Ожидалось: 'Alpha, Beta, Gamma', получено: '{data.get('oldValueText')}'"


# ── Переименование опции ───────────────────────────────────────────────────


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[Select] переименование option: старое событие хранит 'Alpha', новое — 'AlphaRenamed'")
def test_select_cf_rename_option_history(main_client, space_for_history, board_for_history, temp_task, select_custom_field):
    """
    Проверяем корректность valueText в истории после переименования опции:
    1. Выбираем 'Alpha' → событие с valueText='Alpha'
    2. Переименовываем опцию Alpha → AlphaRenamed через EditBoardCustomField
    3. Старое событие сохраняет valueText='Alpha' (название на момент действия)
    4. Очищаем поле и заново выбираем переименованную опцию
    5. Новое событие приходит с valueText='AlphaRenamed' (актуальное название)
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    task_id = temp_task
    field_id = select_custom_field["field_id"]
    opt_a = select_custom_field["opt_a"]
    opt_b = select_custom_field["opt_b"]
    opt_c = select_custom_field["opt_c"]

    with allure.step("Выбираем опцию 'Alpha'"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_a],
        ))
        assert resp.status_code == 200, f"Ошибка при установке кастомного поля: {resp.text}"

    with allure.step("Ожидаем событие с valueText='Alpha'"):
        event_before = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )
        assert event_before["data"]["valueText"] == "Alpha", \
            f"valueText до переименования: '{event_before['data']['valueText']}'"

    with allure.step("Переименовываем опцию Alpha → AlphaRenamed"):
        resp = main_client.post(**edit_board_custom_field_endpoint(
            board_id=board_id, space_id=space_id, field_id=field_id,
            options=[
                {"_id": opt_a, "title": "AlphaRenamed", "color": "red"},
                {"_id": opt_b, "title": "Beta", "color": "blue"},
                {"_id": opt_c, "title": "Gamma", "color": "green"},
            ],
        ))
        assert resp.status_code == 200, f"Ошибка при переименовании опции: {resp.text}"

    with allure.step("Проверяем что старое событие сохранило valueText='Alpha'"):
        event_after = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )
        assert event_after["data"]["valueText"] == "Alpha", \
            f"valueText после переименования изменился! Ожидалось: 'Alpha', получено: '{event_after['data']['valueText']}'"

    with allure.step("Очищаем поле (value=[])"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[],
        ))
        assert resp.status_code == 200, f"Ошибка при очистке поля: {resp.text}"

    with allure.step("Ожидаем событие очистки (isCleared=True)"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": True},
        )

    with allure.step("Заново выбираем переименованную опцию (бывшая 'Alpha')"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value=[opt_a],
        ))
        assert resp.status_code == 200, f"Ошибка при установке опции: {resp.text}"

    with allure.step("Проверяем что новое событие содержит valueText='AlphaRenamed'"):
        event_new = assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
            min_count=2,
        )
        assert event_new["data"]["valueText"] == "AlphaRenamed", \
            f"Новое событие должно содержать актуальное название. Ожидалось: 'AlphaRenamed', получено: '{event_new['data']['valueText']}'"
