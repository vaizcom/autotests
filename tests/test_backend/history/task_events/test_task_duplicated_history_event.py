import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import duplicate_task_endpoint, delete_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("TASK_DUPLICATED event")
def test_task_duplicated_history_event(main_client, space_for_history, board_for_history, temp_task):
    """
    Проверяем генерацию события при дублировании задачи на ту же доску:
    TASK_DUPLICATED (в НОВОЙ скопированной задаче)
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    task_id = temp_task

    with allure.step("1. Дублируем задачу на ту же доску"):
        resp = main_client.post(
            **duplicate_task_endpoint(space_id=space_id, task_id=task_id, board_id=board_id)
        )
        assert resp.status_code == 200, f"Ошибка при дублировании задачи: {resp.text}"
        duplicated_task_id = resp.json()['payload']['task']['_id']

    try:
        with allure.step("Проверяем событие TASK_DUPLICATED у новой задачи: получено и содержит верные данные (_id, sourceId, sourceName)"):
            assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=duplicated_task_id,
                expected_event_key="TASK_DUPLICATED",
                expected_data={"_id": duplicated_task_id, "sourceId": task_id, "sourceName": _TASK_NAME},
            )

    finally:
        with allure.step("Teardown: удаляем сдублированную задачу"):
            main_client.post(**delete_task_endpoint(space_id=space_id, task_id=duplicated_task_id))
