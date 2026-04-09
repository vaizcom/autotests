import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.data.endpoints.Task.task_endpoints import move_single_task_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task Moved Group event")
def test_task_moved_group_history_event(owner_client, main_space, board_with_tasks, temp_task_on_board_with_tasks):
    """
    Проверяем генерацию события при перемещении задачи между колонками (группами) доски:
    TASK_MOVED_GROUP
    """
    task_id = temp_task_on_board_with_tasks

    with allure.step("Setup: Получаем ID второй группы на доске"):
        # Запрашиваем информацию о доске, чтобы найти группу для перемещения
        board_resp = owner_client.post(**get_board_endpoint(board_id=board_with_tasks, space_id=main_space))
        assert board_resp.status_code == 200, f"Ошибка при получении доски: {board_resp.text}"

        groups = board_resp.json()['payload']['board']['groups']
        assert len(groups) > 1, "Для теста перемещения нужно как минимум 2 группы на доске!"

        # Берем ID второй группы (индекс 1), так как задача по умолчанию создается в первой (индекс 0)
        target_group_id = groups[1]['_id']

    with allure.step("1. Перемещаем задачу в другую группу (MoveTasks) -> ожидаем TASK_MOVED_GROUP"):
        # Вызываем перемещение задачи через обертку move_single_task_endpoint
        move_resp = owner_client.post(
            **move_single_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                to_group_id=target_group_id,
                to_index=0  # Ставим на самый верх новой группы
            )
        )
        assert move_resp.status_code == 200, f"Ошибка при перемещении задачи: {move_resp.text}"

        with allure.step("1.1 Проверяем историю задачи -> ожидаем событие с ID новой группы"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_MOVED_GROUP",
                # Ожидаем, что в лог запишется ID группы, в которую переместили задачу.
                expected_data={"groupId": target_group_id}
            )