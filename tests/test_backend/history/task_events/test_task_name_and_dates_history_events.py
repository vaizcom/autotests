import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.task_service.utils import get_current_timestamp, get_due_end
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Name & Due Dates events")
def test_task_name_and_dates_history_events(member_client, main_space, temp_task):
    """
    Проверяем генерацию событий при изменении базовых параметров задачи:
    TASK_RENAMED -> TASK_DUE_CHANGED
    """
    task_id = temp_task

    with allure.step("1. Переименовываем задачу -> ожидаем TASK_RENAMED"):
        new_name = "Updated Task Name for History Test"
        member_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                name=new_name
            )
        )

        assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_RENAMED",
            expected_data={"name": new_name}
        )

    with allure.step("2. Устанавливаем дедлайн (Due Dates) -> ожидаем TASK_DUE_CHANGED"):
        due_start = get_current_timestamp()
        due_end = get_due_end()

        member_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                dueStart=due_start,
                dueEnd=due_end
            )
        )

        event_data = assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_DUE_CHANGED_V2"
        )

        # Сравниваем только первые 19 символов (YYYY-MM-DDTHH:MM:SS)
        assert event_data.get("data").get("dueStart")[:19] == due_start[:19], \
            f"Неверная дата dueStart. Ожидалось: {due_start[:19]}, получено: {event_data.get('data').get('dueStart')[:19]}"
        assert event_data.get("data").get("dueEnd")[:19] == due_end[:19], \
            f"Неверная дата dueEnd. Ожидалось: {due_end[:19]}, получено: {event_data.get('data').get('dueEnd')[:19]}"