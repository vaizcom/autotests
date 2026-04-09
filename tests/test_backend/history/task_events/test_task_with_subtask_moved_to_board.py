import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.data.endpoints.Task.task_endpoints import (
    move_task_to_board_endpoint,
    create_task_endpoint,
    get_task_endpoint,
    delete_task_endpoint
)
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Move to another board: Move Task with Subtask")
def test_task_with_subtask_moved_to_board(owner_client, main_space, board_with_tasks, main_board, temp_task_on_board_with_tasks):
    """
    При перемещении родительской задачи на другую доску:
    1. В Родительской таске лог TASK_MOVED_TO_BOARD
    2. Родитель и подзадача открепляются друг от друга (TASK_DETACHED_AS_SUBTASK / TASK_DETACHED_TO_PARENT)
    3. Подзадача остается на старой доске в старой группе
    """
    parent_task_id = temp_task_on_board_with_tasks
    target_board_id = main_board
    subtask_id = None

    with allure.step("Setup: Создаем подзадачу и получаем целевую группу на другой доске"):
        resp = owner_client.post(
            **create_task_endpoint(
                space_id=main_space,
                board=board_with_tasks,
                name="Subtask for cross-board move test",
                parent_task=parent_task_id
            )
        )
        assert resp.status_code == 200
        subtask_id = resp.json()['payload']['task']['_id']
        subtask_initial_group = resp.json()['payload']['task']['group']

        # Целевая группа на новой доске
        board_resp = owner_client.post(**get_board_endpoint(board_id=target_board_id, space_id=main_space))
        target_group_id = board_resp.json()['payload']['board']['groups'][0]['_id']

    try:
        with allure.step(f"1. Перемещаем родительскую задачу на доску {target_board_id}"):
            move_resp = owner_client.post(
                **move_task_to_board_endpoint(
                    space_id=main_space,
                    task_id=parent_task_id,
                    to_board_id=target_board_id,
                    to_group_id=target_group_id
                )
            )
            assert move_resp.status_code == 200

            with allure.step("1.1 История родителя -> TASK_MOVED_TO_BOARD и TASK_DETACHED_AS_SUBTASK"):
                # Был перемещен
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=parent_task_id,
                    expected_event_key="TASK_MOVED_TO_BOARD",
                    expected_data={"toBoardId": target_board_id}
                )
                # Отвязался от сабтаска
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=parent_task_id,
                    expected_event_key="TASK_DETACHED_AS_SUBTASK",
                    expected_data={"_id": subtask_id}  # Замените ключ, если бэкенд использует subtaskId
                )

            with allure.step("1.2 История подзадачи -> TASK_DETACHED_TO_PARENT"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=subtask_id,
                    expected_event_key="TASK_DETACHED_TO_PARENT",
                    expected_data={"_id": parent_task_id}  # Замените ключ, если бэкенд использует parentId
                )

            with allure.step("1.3 Проверяем, что подзадача осталась на старой доске в своей группе"):
                subtask_resp = owner_client.post(**get_task_endpoint(slug_id=subtask_id, space_id=main_space))
                assert subtask_resp.status_code == 200
                task_data = subtask_resp.json()['payload']['task']

                assert task_data['board'] == board_with_tasks, "БАГ! Подзадача улетела на чужую доску вместе с родителем!"
                assert task_data['group'] == subtask_initial_group, "БАГ! Подзадача сменила группу после открепления!"
                assert task_data.get('parentTask') is None, "БАГ! У подзадачи остался указан parentTask, хотя они на разных досках!"

    finally:
        with allure.step("Teardown: Удаляем подзадачу"):
            if subtask_id:
                owner_client.post(**delete_task_endpoint(space_id=main_space, task_id=subtask_id))