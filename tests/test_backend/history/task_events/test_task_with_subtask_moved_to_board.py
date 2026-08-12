import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.data.endpoints.Task.task_endpoints import (
    move_task_to_board_endpoint,
    create_task_endpoint,
    get_task_endpoint,
    delete_task_endpoint
)
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_PARENT_TASK_NAME = "Temp task for history events"
_SUBTASK_NAME = "Subtask for cross-board move test"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Move to another board: Move Task with Subtask")
def test_task_with_subtask_moved_to_board(main_client, space_for_history, board_for_history, second_board, temp_task):
    """
    При перемещении родительской задачи на другую доску:
    1. В родительской таске лог TASK_MOVED_TO_BOARD
    2. Родитель и подзадача открепляются друг от друга (TASK_DETACHED_AS_SUBTASK / TASK_DETACHED_TO_PARENT)
    3. Подзадача остается на старой доске в старой группе
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    target_board_id = second_board
    parent_task_id = temp_task
    subtask_id = None

    with allure.step("Setup: создаем подзадачу и получаем целевую группу на другой доске"):
        resp = main_client.post(
            **create_task_endpoint(
                space_id=space_id, board=board_id,
                name="Subtask for cross-board move test", parent_task=parent_task_id
            )
        )
        assert resp.status_code == 200
        subtask_id = resp.json()['payload']['task']['_id']
        subtask_initial_group = resp.json()['payload']['task']['group']

        board_resp = main_client.post(**get_board_endpoint(board_id=target_board_id, space_id=space_id))
        target_group_id = board_resp.json()['payload']['board']['groups'][0]['_id']

    try:
        with allure.step("1. Перемещаем родительскую задачу на другую доску"):
            move_resp = main_client.post(
                **move_task_to_board_endpoint(
                    space_id=space_id, task_id=parent_task_id,
                    to_board_id=target_board_id, to_group_id=target_group_id
                )
            )
            assert move_resp.status_code == 200

            with allure.step("Проверяем событие TASK_MOVED_TO_BOARD у родителя: получено и содержит верные данные (_id, name, fromBoardId, toBoardId)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=parent_task_id,
                    expected_event_key="TASK_MOVED_TO_BOARD",
                    expected_data={
                        "_id": parent_task_id,
                        "name": _PARENT_TASK_NAME,
                        "fromBoardId": board_id,
                        "toBoardId": target_board_id,
                    },
                )

            with allure.step("Проверяем событие TASK_DETACHED_AS_SUBTASK у родителя: получено и содержит верные данные (_id, name)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=parent_task_id,
                    expected_event_key="TASK_DETACHED_AS_SUBTASK",
                    expected_data={"_id": subtask_id, "name": _SUBTASK_NAME},
                )

            with allure.step("Проверяем событие TASK_DETACHED_TO_PARENT у подзадачи: получено и содержит верные данные (_id, name)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=subtask_id,
                    expected_event_key="TASK_DETACHED_TO_PARENT",
                    expected_data={"_id": parent_task_id, "name": _PARENT_TASK_NAME},
                )

            with allure.step("Проверяем, что подзадача осталась на старой доске в своей группе"):
                subtask_resp = main_client.post(**get_task_endpoint(slug_id=subtask_id, space_id=space_id))
                assert subtask_resp.status_code == 200
                task_data = subtask_resp.json()['payload']['task']

                assert task_data['board'] == board_id, \
                    "БАГ! Подзадача улетела на чужую доску вместе с родителем!"
                assert task_data['group'] == subtask_initial_group, \
                    "БАГ! Подзадача сменила группу после открепления!"
                assert task_data.get('parentTask') is None, \
                    "БАГ! У подзадачи остался указан parentTask, хотя они на разных досках!"

    finally:
        with allure.step("Teardown: удаляем подзадачу"):
            if subtask_id:
                main_client.post(**delete_task_endpoint(space_id=space_id, task_id=subtask_id))
