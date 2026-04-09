import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.data.endpoints.Task.task_endpoints import move_task_to_board_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task Moved To Board event")
def test_task_moved_to_board_history_event(owner_client, main_space, board_with_tasks, temp_task_on_board_with_tasks,
                                           main_board):
    """
    Проверяем генерацию события при перемещении задачи на другую доску (main_board):
    TASK_MOVED_TO_BOARD
    """
    task_id = temp_task_on_board_with_tasks
    target_board_id = main_board

    with allure.step("Setup: Получаем ID первой группы на целевой доске (main_board)"):
        board_resp = owner_client.post(**get_board_endpoint(board_id=target_board_id, space_id=main_space))
        assert board_resp.status_code == 200, f"Ошибка при получении целевой доски: {board_resp.text}"

        # Берем ID первой группы, куда мы положим задачу при переезде
        target_group_id = board_resp.json()['payload']['board']['groups'][0]['_id']

    with allure.step(f"1. Перемещаем задачу с доски {board_with_tasks} на доску {target_board_id}"):
        move_resp = owner_client.post(
            **move_task_to_board_endpoint(
                space_id=main_space,
                task_id=task_id,
                to_board_id=target_board_id,
                to_group_id=target_group_id
            )
        )
        assert move_resp.status_code == 200, f"Ошибка перемещения задачи: {move_resp.text}"

        with allure.step("1.1 Проверяем историю задачи -> ожидаем TASK_MOVED_TO_BOARD"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_MOVED_TO_BOARD",
                # Ожидаем, что в логе будет указан ID новой доски.
                expected_data={"toBoardId": target_board_id}
            )