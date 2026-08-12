import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, delete_task_endpoint, edit_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Assignee history test"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Assignees events: TASK_ASSIGNED & TASK_UNASSIGNED")
def test_task_assigned_unassigned_events(main_client, space_for_history, board_for_history, history_members):
    """
    Проверяем генерацию событий при назначении и снятии исполнителей:
    TASK_ASSIGNED -> TASK_UNASSIGNED
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]

    create_resp = main_client.post(**create_task_endpoint(
        space_id=space_id, board=board_id, name=_TASK_NAME
    ))
    assert create_resp.status_code == 200, f"Ошибка создания задачи: {create_resp.text}"
    task_id = create_resp.json()["payload"]["task"]["_id"]

    try:
        assignee_1 = history_members['main']
        assignee_2 = history_members['manager']
        assignees = assignee_1 + assignee_2

        with allure.step("1. Назначаем исполнителей"):
            main_client.post(
                **edit_task_endpoint(space_id=space_id, task_id=task_id, assignees=assignees)
            )

            with allure.step("Проверяем событие TASK_ASSIGNED: получено и содержит верные данные (_id, hrid, name, board, members)"):
                event = assert_get_history_event(
                    client=main_client,
                    space_id=space_id,
                    kind="Task",
                    kind_id=task_id,
                    expected_event_key="TASK_ASSIGNED",
                    expected_data={"_id": task_id, "name": _TASK_NAME, "board": board_id, "members": assignees},
                )
                assert isinstance(event["data"].get("hrid"), str), "hrid должен быть строкой"

        with allure.step("2. Снимаем одного исполнителя"):
            main_client.post(
                **edit_task_endpoint(space_id=space_id, task_id=task_id, assignees=assignee_1)
            )

            with allure.step("Проверяем событие TASK_UNASSIGNED: получено и содержит верные данные (_id, hrid, name, board, members)"):
                event = assert_get_history_event(
                    client=main_client,
                    space_id=space_id,
                    kind="Task",
                    kind_id=task_id,
                    expected_event_key="TASK_UNASSIGNED",
                    expected_data={"_id": task_id, "name": _TASK_NAME, "board": board_id, "members": assignee_2},
                )
                assert isinstance(event["data"].get("hrid"), str), "hrid должен быть строкой"
    finally:
        with allure.step("Teardown: удаляем задачу"):
            main_client.post(**delete_task_endpoint(task_id=task_id, space_id=space_id))
