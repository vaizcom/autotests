import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, delete_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("TASK_CREATED event")
def test_task_created_event(main_client, space_for_history, board_for_history):
    """
    Проверяем генерацию события при создании задачи:
    TASK_CREATED
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    task_name = "Task for CREATED event test"

    with allure.step("Создаём задачу"):
        create_resp = main_client.post(
            **create_task_endpoint(space_id=space_id, board=board_id, name=task_name)
        )
        assert create_resp.status_code == 200
        task_id = create_resp.json()['payload']['task']['_id']

    try:
        with allure.step("Проверяем событие TASK_CREATED: получено и содержит верные данные (_id, name)"):
            assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_CREATED",
                expected_data={"_id": task_id, "name": task_name},
            )
    finally:
        with allure.step("Teardown: удаляем задачу"):
            main_client.post(**delete_task_endpoint(space_id=space_id, task_id=task_id))


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("TASK_DELETED event")
def test_task_deleted_event(main_client, space_for_history, board_for_history):
    """
    Проверяем генерацию события при удалении задачи:
    TASK_DELETED (проверяем через kind=Space, т.к. задача удалена)
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]

    with allure.step("Setup: создаём задачу для удаления"):
        create_resp = main_client.post(
            **create_task_endpoint(space_id=space_id, board=board_id, name="Task for DELETED event test")
        )
        assert create_resp.status_code == 200
        task_id = create_resp.json()['payload']['task']['_id']

    with allure.step("Удаляем задачу"):
        delete_resp = main_client.post(
            **delete_task_endpoint(space_id=space_id, task_id=task_id)
        )
        assert delete_resp.status_code == 200

    with allure.step("Проверяем событие TASK_DELETED через kind=Space: получено и содержит верные данные (_id, name)"):
        # Бэкенд не отдает историю для удаленной задачи по kind="Task" (задача удалена).
        # kind="Board" удалён из THistoryKind в APP-5670, используем kind="Space".
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Space",
            kind_id=space_id,
            expected_event_key="TASK_DELETED",
            expected_data={"_id": task_id, "name": "Task for DELETED event test"},
        )
