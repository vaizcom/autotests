import time

import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import create_board_custom_field_endpoint
from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, delete_task_endpoint

_RETRYABLE_ERRORS = ("AccessDenied", "MemberDidNotFound")


def _create_custom_field_with_retry(client, board_id, space_id, name, cf_type, retries=10, delay=3):
    """Создаёт кастомное поле с ретраем на AccessDenied/MemberDidNotFound.
    В CI права могут быть ещё не проиндексированы сразу после создания борды."""
    for attempt in range(retries):
        resp = client.post(**create_board_custom_field_endpoint(
            board_id=board_id, space_id=space_id, name=name, type=cf_type,
        ))
        if resp.status_code == 200:
            return resp
        error_code = resp.json().get("error", {}).get("code", "")
        if error_code in _RETRYABLE_ERRORS and attempt < retries - 1:
            time.sleep(delay)
            continue
        break
    assert resp.status_code == 200, f"Setup: не удалось создать custom field: {resp.text}"
    return resp


@pytest.fixture(scope="session")
def text_custom_field(main_client, space_for_history, board_for_history):
    """Text custom field на board_for_history для тестов CUSTOM_FIELD_CHANGED.
    Создаёт определение поля на борде (без значения) — значение устанавливается
    на конкретной задаче через edit_task_custom_field_endpoint."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_text"
    with allure.step(f"Setup: создаём Text custom field '{field_name}'"):
        resp = _create_custom_field_with_retry(
            main_client, board_id, space_id, field_name, "Text",
        )
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {"field_id": field_id, "field_name": field_name}


@pytest.fixture(scope="session")
def date_custom_field(main_client, space_for_history, board_for_history):
    """Date custom field на board_for_history для тестов CUSTOM_FIELD_CHANGED.
    Создаёт определение поля на борде (без значения) — значение устанавливается
    на конкретной задаче через edit_task_custom_field_endpoint."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_date"
    with allure.step(f"Setup: создаём Date custom field '{field_name}'"):
        resp = _create_custom_field_with_retry(
            main_client, board_id, space_id, field_name, "Date",
        )
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {"field_id": field_id, "field_name": field_name}


@pytest.fixture(scope="session")
def boolean_custom_field(main_client, space_for_history, board_for_history):
    """Checkbox custom field на board_for_history для тестов CUSTOM_FIELD_CHANGED.
    API тип "Checkbox" (в UI — Boolean). Создаёт определение поля на борде (без значения) —
    значение устанавливается на конкретной задаче через edit_task_custom_field_endpoint."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_boolean"
    with allure.step(f"Setup: создаём Checkbox custom field '{field_name}'"):
        resp = _create_custom_field_with_retry(
            main_client, board_id, space_id, field_name, "Checkbox",
        )
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {"field_id": field_id, "field_name": field_name}


@pytest.fixture(scope="session")
def member_custom_field(main_client, space_for_history, board_for_history):
    """Member custom field на board_for_history для тестов CUSTOM_FIELD_CHANGED.
    Создаёт определение поля на борде (без значения) — значение устанавливается
    на конкретной задаче через edit_task_custom_field_endpoint.
    Значение — массив member ID."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_member"
    with allure.step(f"Setup: создаём Member custom field '{field_name}'"):
        resp = _create_custom_field_with_retry(
            main_client, board_id, space_id, field_name, "Member",
        )
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {"field_id": field_id, "field_name": field_name}


@pytest.fixture(scope="session")
def estimation_custom_field(main_client, space_for_history, board_for_history):
    """Estimation custom field на board_for_history для тестов CUSTOM_FIELD_CHANGED.
    Значение — ISO 8601 Duration (например "P1W", "PT5H30M").
    В valueText приходит человекочитаемый формат ("1w", "5h 30m")."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_estimation"
    with allure.step(f"Setup: создаём Estimation custom field '{field_name}'"):
        resp = _create_custom_field_with_retry(
            main_client, board_id, space_id, field_name, "Estimation",
        )
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {"field_id": field_id, "field_name": field_name}


@pytest.fixture(scope="session")
def select_custom_field(main_client, space_for_history, board_for_history):
    """Select custom field с тремя опциями на board_for_history.
    Значение — массив option ID. В valueText приходят названия через ', '."""
    from config.generators import generate_object_id
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_select"
    opt_a = generate_object_id()
    opt_b = generate_object_id()
    opt_c = generate_object_id()
    options = [
        {"_id": opt_a, "title": "Alpha", "color": "red"},
        {"_id": opt_b, "title": "Beta", "color": "blue"},
        {"_id": opt_c, "title": "Gamma", "color": "green"},
    ]
    with allure.step(f"Setup: создаём Select custom field '{field_name}' с 3 опциями"):
        for attempt in range(10):
            resp = main_client.post(**create_board_custom_field_endpoint(
                board_id=board_id, space_id=space_id, name=field_name, type="Select",
                options=options,
            ))
            if resp.status_code == 200:
                break
            error_code = resp.json().get("error", {}).get("code", "")
            if error_code in _RETRYABLE_ERRORS and attempt < 9:
                time.sleep(3)
                continue
            break
        assert resp.status_code == 200, f"Setup: не удалось создать custom field: {resp.text}"
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {
        "field_id": field_id, "field_name": field_name,
        "opt_a": opt_a, "opt_b": opt_b, "opt_c": opt_c,
    }


@pytest.fixture(scope="session")
def url_custom_field(main_client, space_for_history, board_for_history):
    """Url custom field на board_for_history для тестов CUSTOM_FIELD_CHANGED.
    Значение — строка (URL). Очистка через пустую строку."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_url"
    with allure.step(f"Setup: создаём Url custom field '{field_name}'"):
        resp = _create_custom_field_with_retry(
            main_client, board_id, space_id, field_name, "Url",
        )
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {"field_id": field_id, "field_name": field_name}


@pytest.fixture(scope="session")
def task_relations_custom_field(main_client, space_for_history, board_for_history):
    """TaskRelations custom field на board_for_history для тестов CUSTOM_FIELD_CHANGED.
    Значение — массив task ID. Очистка через пустой массив []."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_task_relations"
    with allure.step(f"Setup: создаём TaskRelations custom field '{field_name}'"):
        resp = _create_custom_field_with_retry(
            main_client, board_id, space_id, field_name, "TaskRelations",
        )
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {"field_id": field_id, "field_name": field_name}


@pytest.fixture
def linked_tasks(main_client, space_for_history, board_for_history):
    """Две задачи для линковки через TaskRelations CF. Удаляются после теста."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    tasks = []
    for name in ("Linked task A", "Linked task B"):
        for attempt in range(5):
            resp = main_client.post(**create_task_endpoint(
                space_id=space_id, board=board_id, name=name,
            ))
            if resp.status_code == 200:
                break
            error_code = resp.json().get("error", {}).get("code", "")
            if error_code == "MemberDidNotFound" and attempt < 4:
                time.sleep(2)
                continue
            break
        assert resp.status_code == 200, f"Setup: не удалось создать '{name}': {resp.text}"
        task = resp.json()["payload"]["task"]
        tasks.append({"task_id": task["_id"], "name": name})

    yield tasks

    for t in tasks:
        main_client.post(**delete_task_endpoint(space_id=space_id, task_id=t["task_id"]))


@pytest.fixture(scope="session")
def text_custom_field_2(main_client, space_for_history, board_for_history):
    """Второй Text CF на board_for_history — для теста различимости одинаковых типов."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_text_2"
    with allure.step(f"Setup: создаём второй Text custom field '{field_name}'"):
        resp = _create_custom_field_with_retry(
            main_client, board_id, space_id, field_name, "Text",
        )
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {"field_id": field_id, "field_name": field_name}


@pytest.fixture(scope="session")
def number_custom_field(main_client, space_for_history, board_for_history):
    """Number custom field на board_for_history для тестов CUSTOM_FIELD_CHANGED.
    Создаёт определение поля на борде (без значения) — значение устанавливается
    на конкретной задаче через edit_task_custom_field_endpoint."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_number"
    with allure.step(f"Setup: создаём Number custom field '{field_name}'"):
        resp = _create_custom_field_with_retry(
            main_client, board_id, space_id, field_name, "Number",
        )
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {"field_id": field_id, "field_name": field_name}
