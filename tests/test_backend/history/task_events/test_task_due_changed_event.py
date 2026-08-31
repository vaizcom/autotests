import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.task_service.utils import get_current_timestamp, get_due_end
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("TASK_DUE_CHANGED_V2 event")
def test_task_due_changed_event(main_client, space_for_history, board_for_history, project_for_history, temp_task):
    """
    Проверяем генерацию события при изменении дедлайна задачи:
    TASK_DUE_CHANGED_V2
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    project_id = project_for_history["project_id"]
    task_id = temp_task

    with allure.step("Устанавливаем дедлайн (Due Dates)"):
        due_start = get_current_timestamp()
        due_end = get_due_end()

        main_client.post(
            **edit_task_endpoint(space_id=space_id, task_id=task_id, dueStart=due_start, dueEnd=due_end)
        )

        with allure.step("Проверяем событие TASK_DUE_CHANGED_V2: получено и содержит верные данные (_id, name, board, project, dueStart, dueEnd)"):
            event_data = assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_DUE_CHANGED_V2",
                expected_data={
                    "_id": task_id,
                    "name": "Temp task for history events",
                    "board": board_id,
                    "project": project_id,
                },
            )

            # dueStart/dueEnd сравниваем по дате (YYYY-MM-DD) — бэкенд нормализует время (dueStart → 00:00:00, dueEnd → 23:59:59)
            assert event_data.get("data").get("dueStart")[:10] == due_start[:10], \
                f"Неверная дата dueStart. Ожидалось: {due_start[:10]}, получено: {event_data.get('data').get('dueStart')[:10]}"
            assert event_data.get("data").get("dueEnd")[:10] == due_end[:10], \
                f"Неверная дата dueEnd. Ожидалось: {due_end[:10]}, получено: {event_data.get('data').get('dueEnd')[:10]}"
