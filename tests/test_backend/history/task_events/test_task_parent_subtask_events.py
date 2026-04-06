import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, toggle_subtask_endpoint, \
    delete_task_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Parent & Subtask events")
def test_task_parent_subtask_history_events(owner_client, main_space, main_board, temp_task):
    """
    Проверяем генерацию событий при связывании задач (Родитель - Подзадача):
    TASK_ATTACHED_AS_SUBTASK / TASK_ATTACHED_TO_PARENT
    И события открепления:
    TASK_DETACHED_AS_SUBTASK / TASK_DETACHED_TO_PARENT
    (при отвязке через ToggleSubtask)
    """
    parent_task_id = temp_task

    with allure.step("1. Создаем подзадачу, сразу указывая parent_task -> ожидаем ATTACHED"):
        resp = owner_client.post(
            **create_task_endpoint(
                space_id=main_space,
                board=main_board,
                name="Subtask for hierarchy test",
                parent_task=parent_task_id
            )
        )
        assert resp.status_code == 200, f"Ошибка создания подзадачи: {resp.text}"
        subtask_id = resp.json()['payload']['task']['_id']

    try:
        with allure.step("1.1 Проверяем историю родительской задачи (появился сабтаск)"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Task",
                kind_id=parent_task_id,
                expected_event_key="TASK_ATTACHED_AS_SUBTASK",
                # Ожидаем, что в данных указан ID привязанной подзадачи
                expected_data={"_id": subtask_id}
            )

        with allure.step("1.2 Проверяем историю самой подзадачи (прикрепилась к родителю)"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Task",
                kind_id=subtask_id,
                expected_event_key="TASK_ATTACHED_TO_PARENT",
                # Ожидаем, что в данных указан ID родителя
                expected_data={"_id": parent_task_id}
            )

        with allure.step("2. Отвязываем подзадачу (ToggleSubtask) -> ожидаем DETACHED"):
            toggle_resp = owner_client.post(
                **toggle_subtask_endpoint(
                    space_id=main_space,
                    task_id=subtask_id,
                    parent_task_id=None  # Отвязываем от родителя
                )
            )
            assert toggle_resp.status_code == 200, f"Ошибка при отвязке подзадачи: {toggle_resp.text}"

            with allure.step("2.1 Проверяем историю родителя (сабтаск отвязан)"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=parent_task_id,
                    expected_event_key="TASK_DETACHED_AS_SUBTASK",
                    expected_data={"_id": subtask_id}
                )

            with allure.step("2.2 Проверяем историю подзадачи (родитель отвязан)"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=subtask_id,
                    expected_event_key="TASK_DETACHED_TO_PARENT",
                    expected_data={"_id": parent_task_id}
                )

    finally:
        with allure.step("Teardown: Удаление созданной подзадачи"):
            # Удаляем подзадачу, чтобы не мусорить в базе
            owner_client.post(
                **delete_task_endpoint(
                    space_id=main_space,
                    task_id=subtask_id
                )
            )