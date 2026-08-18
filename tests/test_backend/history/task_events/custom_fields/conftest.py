import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import create_board_custom_field_endpoint


@pytest.fixture(scope="session")
def text_custom_field(main_client, space_for_history, board_for_history):
    """Text custom field на board_for_history для тестов CUSTOM_FIELD_CHANGED.
    Создаёт определение поля на борде (без значения) — значение устанавливается
    на конкретной задаче через edit_task_custom_field_endpoint."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    field_name = "cf_history_text"
    with allure.step(f"Setup: создаём Text custom field '{field_name}'"):
        resp = main_client.post(**create_board_custom_field_endpoint(
            board_id=board_id, space_id=space_id, name=field_name, type="Text",
        ))
        assert resp.status_code == 200, f"Setup: не удалось создать custom field: {resp.text}"
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
        resp = main_client.post(**create_board_custom_field_endpoint(
            board_id=board_id, space_id=space_id, name=field_name, type="Number",
        ))
        assert resp.status_code == 200, f"Setup: не удалось создать custom field: {resp.text}"
        field_id = resp.json()["payload"]["customField"]["_id"]
    yield {"field_id": field_id, "field_name": field_name}
