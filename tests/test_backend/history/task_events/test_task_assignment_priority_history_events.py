import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend, pytest.mark.history]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Assignees & Priority events")
def test_task_assignment_priority_history_events(member_client, main_space, temp_task, random_main_personal_id):
    """
    Проверяем генерацию событий:
    TASK_ASSIGNED -> TASK_UNASSIGNED -> TASK_PRIORITY_CHANGED
    """
    task_id = temp_task

    with allure.step("1. Назначаем исполнителя -> ожидаем TASK_ASSIGNED"):
        member_client.post(
            **edit_task_endpoint(space_id=main_space, task_id=task_id, assignees=[random_main_personal_id])
        )

        assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_ASSIGNED"
        )

    with allure.step("2. Снимаем исполнителя (передаем пустой список) -> ожидаем TASK_UNASSIGNED"):
        member_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                assignees=[]  # Пустой список снимает всех назначенных пользователей
            )
        )

        assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_UNASSIGNED"
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
            expected_event_key="TASK_PRIORITY_CHANGED"
        )