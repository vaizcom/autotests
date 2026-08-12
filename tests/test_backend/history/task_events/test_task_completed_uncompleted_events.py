import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("TASK_COMPLETED & TASK_UNCOMPLETED events")
def test_task_completed_uncompleted_events(main_client, space_for_history, board_for_history, project_for_history, temp_task):
    """
    Проверяем генерацию событий при завершении и возврате задачи:
    TASK_COMPLETED -> TASK_UNCOMPLETED
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    project_id = project_for_history["project_id"]
    task_id = temp_task

    expected_data = {
        "_id": task_id,
        "name": "Temp task for history events",
        "board": board_id,
        "project": project_id,
    }

    with allure.step("1. Завершаем задачу (completed=True)"):
        complete_resp = main_client.post(
            **edit_task_endpoint(space_id=space_id, task_id=task_id, completed=True)
        )
        assert complete_resp.status_code == 200

        with allure.step("Проверяем событие TASK_COMPLETED: получено и содержит верные данные (_id, name, board, project)"):
            assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_COMPLETED",
                expected_data=expected_data,
            )

    with allure.step("2. Возвращаем задачу (completed=False)"):
        uncomplete_resp = main_client.post(
            **edit_task_endpoint(space_id=space_id, task_id=task_id, completed=False)
        )
        assert uncomplete_resp.status_code == 200

        with allure.step("Проверяем событие TASK_UNCOMPLETED: получено и содержит верные данные (_id, name, board, project)"):
            assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_UNCOMPLETED",
                expected_data=expected_data,
            )
