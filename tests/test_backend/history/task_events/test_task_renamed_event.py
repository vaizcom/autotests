import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_OLD_TASK_NAME = "Temp task for history events"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("TASK_RENAMED event")
def test_task_renamed_event(main_client, space_for_history, temp_task):
    """
    Проверяем генерацию события при переименовании задачи:
    TASK_RENAMED
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    new_name = "Updated Task Name for History Test"

    with allure.step("Переименовываем задачу"):
        main_client.post(
            **edit_task_endpoint(space_id=space_id, task_id=task_id, name=new_name)
        )

        with allure.step("Проверяем событие TASK_RENAMED: получено и содержит верные данные (_id, hrid, name, oldName)"):
            event = assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_RENAMED",
                expected_data={"_id": task_id, "name": new_name, "oldName": _OLD_TASK_NAME},
            )
            assert isinstance(event["data"].get("hrid"), str), "hrid должен быть строкой"
