import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Priority event: TASK_PRIORITY_CHANGED")
def test_task_priority_changed_event(main_client, space_for_history, temp_task):
    """
    Проверяем генерацию события при изменении приоритета задачи:
    TASK_PRIORITY_CHANGED
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task

    with allure.step("Меняем приоритет задачи"):
        main_client.post(
            **edit_task_endpoint(space_id=space_id, task_id=task_id, priority=2)
        )

        with allure.step("Проверяем событие TASK_PRIORITY_CHANGED: получено и содержит верные данные (_id, hrid, name, taskPriority)"):
            event = assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_PRIORITY_CHANGED",
                expected_data={"_id": task_id, "name": _TASK_NAME, "taskPriority": 2},
            )
            assert isinstance(event["data"].get("hrid"), str), "hrid должен быть строкой"
