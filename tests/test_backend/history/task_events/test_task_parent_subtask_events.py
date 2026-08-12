import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, toggle_subtask_endpoint, \
    delete_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event, assert_history_event_count

pytestmark = [pytest.mark.backend]

_PARENT_TASK_NAME = "Temp task for history events"
_SUBTASK_NAME = "Subtask for hierarchy test"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Parent & Subtask events: ATTACHED / DETACHED")
def test_task_parent_subtask_history_events(main_client, space_for_history, board_for_history, temp_task):
    """
    Проверяем генерацию событий при связывании задач (Родитель - Подзадача):
    TASK_ATTACHED_AS_SUBTASK / TASK_ATTACHED_TO_PARENT
    И события открепления:
    TASK_DETACHED_AS_SUBTASK / TASK_DETACHED_TO_PARENT
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    parent_task_id = temp_task

    with allure.step("1. Создаем подзадачу, указывая parent_task"):
        resp = main_client.post(
            **create_task_endpoint(
                space_id=space_id, board=board_id,
                name=_SUBTASK_NAME, parent_task=parent_task_id
            )
        )
        assert resp.status_code == 200, f"Ошибка создания подзадачи: {resp.text}"
        subtask_id = resp.json()['payload']['task']['_id']

    try:
        with allure.step("Проверяем событие TASK_ATTACHED_AS_SUBTASK у родителя: получено и содержит верные данные (_id, name)"):
            assert_get_history_event(
                client=main_client, space_id=space_id,
                kind="Task", kind_id=parent_task_id,
                expected_event_key="TASK_ATTACHED_AS_SUBTASK",
                expected_data={"_id": subtask_id, "name": _SUBTASK_NAME},
            )

        with allure.step("Проверяем событие TASK_ATTACHED_TO_PARENT у подзадачи: получено и содержит верные данные (_id, name)"):
            assert_get_history_event(
                client=main_client, space_id=space_id,
                kind="Task", kind_id=subtask_id,
                expected_event_key="TASK_ATTACHED_TO_PARENT",
                expected_data={"_id": parent_task_id, "name": _PARENT_TASK_NAME},
            )

        with allure.step("Проверяем что событие TASK_ATTACHED_TO_PARENT не дублируется"):
            assert_history_event_count(
                client=main_client, space_id=space_id,
                kind="Task", kind_id=subtask_id,
                event_key="TASK_ATTACHED_TO_PARENT",
                expected_count=1,
            )

        with allure.step("2. Отвязываем подзадачу (ToggleSubtask)"):
            toggle_resp = main_client.post(
                **toggle_subtask_endpoint(
                    space_id=space_id, task_id=subtask_id, parent_task_id=None
                )
            )
            assert toggle_resp.status_code == 200, f"Ошибка при отвязке подзадачи: {toggle_resp.text}"

            with allure.step("Проверяем событие TASK_DETACHED_AS_SUBTASK у родителя: получено и содержит верные данные (_id, name)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=parent_task_id,
                    expected_event_key="TASK_DETACHED_AS_SUBTASK",
                    expected_data={"_id": subtask_id, "name": _SUBTASK_NAME},
                )

            with allure.step("Проверяем событие TASK_DETACHED_TO_PARENT у подзадачи: получено и содержит верные данные (_id, name)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=subtask_id,
                    expected_event_key="TASK_DETACHED_TO_PARENT",
                    expected_data={"_id": parent_task_id, "name": _PARENT_TASK_NAME},
                )

    finally:
        with allure.step("Teardown: удаляем подзадачу"):
            main_client.post(**delete_task_endpoint(space_id=space_id, task_id=subtask_id))
