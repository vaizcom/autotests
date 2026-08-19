import time

import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import create_board_custom_field_endpoint

_RETRYABLE_ERRORS = ("AccessDenied", "MemberDidNotFound")


def _create_custom_field_with_retry(client, board_id, space_id, name, cf_type, retries=5, delay=2):
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
        for attempt in range(5):
            resp = main_client.post(**create_board_custom_field_endpoint(
                board_id=board_id, space_id=space_id, name=field_name, type="Select",
                options=options,
            ))
            if resp.status_code == 200:
                break
            error_code = resp.json().get("error", {}).get("code", "")
            if error_code in _RETRYABLE_ERRORS and attempt < 4:
                time.sleep(2)
                continue
            break
        assert resp.status_code == 200, f"Setup: не удалось создать custom field: {resp.text}"
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {
        "field_id": field_id, "field_name": field_name,
        "opt_a": opt_a, "opt_b": opt_b, "opt_c": opt_c,
    }


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
