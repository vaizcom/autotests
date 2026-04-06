import allure
import pytest

from conftest import board_with_tasks
from test_backend.data.endpoints.Task.task_endpoints import duplicate_task_endpoint, delete_task_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task Duplicated event")
def test_task_duplicated_history_event(owner_client, main_space, board_with_tasks, temp_task):
    """
    Проверяем генерацию события при дублировании задачи на ту же доску:
    (!! апи позволяет передать любой boardId, фронт только текущую доску)
    TASK_DUPLICATED (в НОВОЙ скопированной задаче)
    """
    task_id = temp_task

    with allure.step("1. Дублируем задачу на ту же доску -> ожидаем TASK_DUPLICATED"):
        resp = owner_client.post(
            **duplicate_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                board_id=board_with_tasks # !! апи позволяет передать любой boardId, фронт только текущую доску
            )
        )
        assert resp.status_code == 200, f"Ошибка при дублировании задачи: {resp.text}"

        # Получаем ID новой (сдублированной) задачи, чтобы потом её удалить
        duplicated_task_id = resp.json()['payload']['task']['_id']

    try:
        with allure.step("1.1 Проверяем историю НОВОЙ задачи (что её сдублировали)"):
            # Запрашиваем историю оригинала
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Task",
                kind_id=duplicated_task_id,  # Смотрим историю сдублированной задачи
                expected_event_key="TASK_DUPLICATED",
                # Ожидаем увидеть ID оригинальной задачи в логах новой.
                expected_data={"sourceId": task_id}
            )

    finally:
        with allure.step("Teardown: Удаляем сдублированную задачу"):
            owner_client.post(
                **delete_task_endpoint(
                    space_id=main_space,
                    task_id=duplicated_task_id
                )
            )