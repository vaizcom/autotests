import allure
import pytest

from test_backend.data.endpoints.Board.board_endpoints import get_board_endpoint
from test_backend.data.endpoints.Task.task_endpoints import (
    move_single_task_endpoint,
    create_task_endpoint,
    get_task_endpoint,
    delete_task_endpoint
)
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Move to another group: Move Task with Subtask")
def test_task_with_subtask_moved_group(owner_client, main_space, board_with_tasks, temp_task_on_board_with_tasks):
    """
    При перемещении родительской задачи в другую группу:
    1. Родитель генерирует событие TASK_MOVED_GROUP
    2. Подзадача НЕ перемещается вместе с ней (остается в старой группе)
    """
    parent_task_id = temp_task_on_board_with_tasks
    subtask_id = None

    with allure.step("Setup: Создаем подзадачу для родительской задачи"):
        resp = owner_client.post(
            **create_task_endpoint(
                space_id=main_space,
                board=board_with_tasks,
                name="Subtask for move group test",
                parent_task=parent_task_id
            )
        )
        assert resp.status_code == 200
        subtask_id = resp.json()['payload']['task']['_id']
        subtask_initial_group = resp.json()['payload']['task']['group']

        # Получаем ID второй группы на доске для перемещения родителя
        board_resp = owner_client.post(**get_board_endpoint(board_id=board_with_tasks, space_id=main_space))
        groups = board_resp.json()['payload']['board']['groups']
        target_group_id = groups[1]['_id']

    try:
        with allure.step("1. Перемещаем родительскую задачу в другую группу (MoveTasks)"):
            owner_client.post(
                **move_single_task_endpoint(
                    space_id=main_space,
                    task_id=parent_task_id,
                    to_group_id=target_group_id
                )
            )

            with allure.step("1.1 Проверяем историю родителя -> TASK_MOVED_GROUP"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=parent_task_id,
                    expected_event_key="TASK_MOVED_GROUP",
                    expected_data={"groupId": target_group_id}
                )

            with allure.step("1.2 Проверяем, что подзадача осталась в своей изначальной группе"):
                # Получаем актуальное состояние подзадачи
                subtask_resp = owner_client.post(**get_task_endpoint(slug_id=subtask_id, space_id=main_space))
                assert subtask_resp.status_code == 200
                current_subtask_group = subtask_resp.json()['payload']['task']['group']

                assert current_subtask_group == subtask_initial_group, \
                    f"БАГ! Подзадача переместилась вместе с родителем. Ожидалась группа {subtask_initial_group}, получена {current_subtask_group}"

    finally:
        with allure.step("Teardown: Удаляем подзадачу"):
            if subtask_id:
                owner_client.post(**delete_task_endpoint(space_id=main_space, task_id=subtask_id))