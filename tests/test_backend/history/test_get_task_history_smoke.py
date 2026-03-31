import allure
import pytest

from conftest import owner_client
from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, edit_task_endpoint, \
    delete_task_endpoint
# Импортируем нашу новую утилиту
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend, pytest.mark.history]


@allure.epic("History")
@allure.feature("Task History")
@allure.story("Группа 1: Базовый жизненный цикл задачи (Life cycle)")
def test_task_lifecycle_history_events(member_client, main_space, board_with_tasks, owner_client):
    """
    Проверяем генерацию базовых событий жизненного цикла задачи:
    TASK_CREATED -> TASK_COMPLETED -> TASK_UNCOMPLETED -> TASK_DELETED
    """

    with allure.step("1. Создание задачи -> ожидаем TASK_CREATED"):
        task_name = "Lifecycle task"
        create_resp = member_client.post(
            **create_task_endpoint(
                space_id=main_space,
                board=board_with_tasks,
                name=task_name
            )
        )
        assert create_resp.status_code == 200
        task_id = create_resp.json()['payload']['task']['_id']

        assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_CREATED"
        )

    with allure.step("2. Выполнение задачи -> ожидаем TASK_COMPLETED"):
        complete_resp = member_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                completed=True
            )
        )
        assert complete_resp.status_code == 200

        assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_COMPLETED"
        )

    with allure.step("3. Отмена выполнения задачи -> ожидаем TASK_UNCOMPLETED"):
        uncomplete_resp = member_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                completed=False
            )
        )
        assert uncomplete_resp.status_code == 200

        assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_UNCOMPLETED"
        )

    with allure.step("4. Удаление задачи -> ожидаем TASK_DELETED"):
        delete_resp = owner_client.post(
            **delete_task_endpoint(
                space_id=main_space,
                task_id=task_id
            )
        )
        assert delete_resp.status_code == 200

        # Бэкенд не отдает историю для удаленной задачи по kind="Task",
        # здесь поменяли kind="Board" и kind_id=board_with_tasks
        deleted_event = assert_history_event_exists(
            client=member_client,
            space_id=main_space,
            kind="Board",
            kind_id=board_with_tasks,
            expected_event_key="TASK_DELETED"
        )

        # Дополнительно проверяем, что ивент удаления принадлежит именно нашей задаче
        assert deleted_event.get("taskId") == task_id, (
            f"Ивент удаления принадлежит другой задаче. Ожидался: {task_id}, получен: {deleted_event.get('taskId')}"
        )