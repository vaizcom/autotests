import allure
import pytest

from test_backend.data.endpoints.archive.archive_task_endpoint import archive_task_endpoint
from test_backend.data.endpoints.archive.unarchive_task_endpoint import unarchive_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("TASK_ARCHIVED & TASK_UNARCHIVED events")
def test_task_archived_unarchived_events(
    main_client, space_for_history, board_for_history, project_for_history, temp_task
):
    """
    Проверяем генерацию событий при архивации и разархивации задачи:
    TASK_ARCHIVED -> TASK_UNARCHIVED

    data содержит: _id, hrid, name, board, title, project.
    hrid проверяется только как строка — значение недоступно без дополнительного запроса.
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    project_id = project_for_history["project_id"]
    task_id = temp_task

    expected_data = {
        "_id": task_id,
        "name": _TASK_NAME,
        "title": _TASK_NAME,
        "board": board_id,
        "project": project_id,
    }

    with allure.step("1. Архивируем задачу"):
        archive_resp = main_client.post(
            **archive_task_endpoint(task_id=task_id, space_id=space_id)
        )
        assert archive_resp.status_code == 200, f"Ошибка архивации: {archive_resp.text}"

        with allure.step("Проверяем событие TASK_ARCHIVED: получено и содержит верные данные (_id, hrid, name, title, board, project)"):
            event = assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_ARCHIVED",
                expected_data=expected_data,
            )
            assert isinstance(event["data"].get("hrid"), str), "hrid должен быть строкой"

    with allure.step("2. Разархивируем задачу"):
        unarchive_resp = main_client.post(
            **unarchive_task_endpoint(task_id=task_id, space_id=space_id)
        )
        assert unarchive_resp.status_code == 200, f"Ошибка разархивации: {unarchive_resp.text}"

        with allure.step("Проверяем событие TASK_UNARCHIVED: получено и содержит верные данные (_id, hrid, name, title, board, project)"):
            event = assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_UNARCHIVED",
                expected_data=expected_data,
            )
            assert isinstance(event["data"].get("hrid"), str), "hrid должен быть строкой"
