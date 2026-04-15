import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Assignees & Priority events")
def test_task_assignment_priority_history_events(member_client, main_space, temp_task_on_board_with_tasks, main_personal):
    """
    Проверяем генерацию событий:
    TASK_ASSIGNED -> TASK_UNASSIGNED -> TASK_PRIORITY_CHANGED
    """
    task_id = temp_task_on_board_with_tasks
    assignee_1 = main_personal['member']
    assignee_2 = main_personal['manager']
    assignees = assignee_1 + assignee_2


    with allure.step("1. Назначаем исполнителя -> ожидаем TASK_ASSIGNED"):
        member_client.post(
            **edit_task_endpoint(space_id=main_space, task_id=task_id, assignees=assignees)
        )

        assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_ASSIGNED",
            expected_data={"members": assignees}
        )

    with allure.step("2. Снимаем исполнителя (передаем пустой список) -> ожидаем TASK_UNASSIGNED"):
        member_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                assignees=assignee_1
            )
        )

        assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_UNASSIGNED",
            expected_data={"members": assignee_2}
        )

    with allure.step("3. Меняем приоритет -> ожидаем TASK_PRIORITY_CHANGED"):
        member_client.post(
            **edit_task_endpoint(space_id=main_space, task_id=task_id, priority=2)
        )

        assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_PRIORITY_CHANGED",
            expected_data={"taskPriority": 2}
        )