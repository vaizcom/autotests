import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, delete_task_endpoint, edit_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_history_event_exists
from core.response_utils import short_resp

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Assignees & Priority events")
def test_task_assignment_priority_history_events(owner_client, member_client, main_space, board_with_tasks, main_personal):
    """
    Проверяем генерацию событий:
    TASK_ASSIGNED -> TASK_UNASSIGNED -> TASK_PRIORITY_CHANGED
    Тест использует board_with_tasks, т.к. member_client имеет доступ к этой борде.
    """
    create_resp = member_client.post(**create_task_endpoint(
        space_id=main_space, board=board_with_tasks, name="Assignment priority history test"
    ))
    assert create_resp.status_code == 200, f"Ошибка создания задачи: {short_resp(create_resp)}"
    task_id = create_resp.json()["payload"]["task"]["_id"]

    try:
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
    finally:
        owner_client.post(**delete_task_endpoint(task_id=task_id, space_id=main_space))
