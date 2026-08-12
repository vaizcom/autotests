import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.data.endpoints.Task.task_endpoints import (
    move_single_task_endpoint,
    create_task_endpoint,
    get_task_endpoint,
    delete_task_endpoint
)
from test_backend.data.endpoints.History.history_utils import assert_get_history_event, assert_history_event_count

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Move to another group: Move Task with Subtask")
def test_task_with_subtask_moved_group(main_client, space_for_history, board_for_history, project_for_history, temp_task):
    """
    При перемещении родительской задачи в другую группу:
    1. Родитель генерирует событие TASK_MOVED_GROUP
    2. Подзадача НЕ перемещается вместе с ней (остается в старой группе)
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    project_id = project_for_history["project_id"]
    parent_task_id = temp_task
    subtask_id = None

    with allure.step("Setup: создаем подзадачу и получаем целевую группу"):
        resp = main_client.post(
            **create_task_endpoint(
                space_id=space_id, board=board_id,
                name="Subtask for move group test", parent_task=parent_task_id
            )
        )
        assert resp.status_code == 200
        subtask_id = resp.json()['payload']['task']['_id']
        subtask_initial_group = resp.json()['payload']['task']['group']

        board_resp = main_client.post(**get_board_endpoint(board_id=board_id, space_id=space_id))
        groups = board_resp.json()['payload']['board']['groups']
        target_group_id = groups[1]['_id']
        target_group_name = groups[1]['name']

    try:
        with allure.step("1. Перемещаем родительскую задачу в другую группу"):
            move_resp = main_client.post(
                **move_single_task_endpoint(
                    space_id=space_id, task_id=parent_task_id, to_group_id=target_group_id
                )
            )
            assert move_resp.status_code == 200, f"Ошибка перемещения: {move_resp.text}"

            with allure.step("Проверяем событие TASK_MOVED_GROUP: получено и содержит верные данные (_id, name, board, project, groupId, groupName)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=parent_task_id,
                    expected_event_key="TASK_MOVED_GROUP",
                    expected_data={
                        "_id": parent_task_id,
                        "name": _TASK_NAME,
                        "board": board_id,
                        "project": project_id,
                        "groupId": target_group_id,
                        "groupName": target_group_name,
                    },
                )

            with allure.step("Проверяем что событие TASK_MOVED_GROUP не дублируется"):
                assert_history_event_count(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=parent_task_id,
                    event_key="TASK_MOVED_GROUP",
                    expected_count=1,
                )

            with allure.step("Проверяем, что подзадача осталась в изначальной группе"):
                subtask_resp = main_client.post(**get_task_endpoint(slug_id=subtask_id, space_id=space_id))
                assert subtask_resp.status_code == 200
                current_subtask_group = subtask_resp.json()['payload']['task']['group']

                assert current_subtask_group == subtask_initial_group, \
                    f"БАГ! Подзадача переместилась вместе с родителем. " \
                    f"Ожидалась группа {subtask_initial_group}, получена {current_subtask_group}"

    finally:
        with allure.step("Teardown: удаляем подзадачу"):
            if subtask_id:
                main_client.post(**delete_task_endpoint(space_id=space_id, task_id=subtask_id))
