import allure
import pytest

from conftest import board_with_tasks
from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task Types events")
def test_task_types_history_events(owner_client, main_space, temp_task_on_board_with_tasks, board_with_tasks):
    """
    Проверяем генерацию событий при работе с массивом типов задачи (Types):
    TASK_TYPE_ADDED -> TASK_TYPE_ADDED (еще один) -> TASK_TYPE_REMOVED -> TASK_TYPE_CHANGED
    """
    task_id = temp_task_on_board_with_tasks

    # Получаем два разных типа для доски
    # type_1 = get_random_type_id(owner_client, board_with_tasks, main_space)
    # type_2 = get_random_type_id(owner_client, board_with_tasks, main_space)
    # while type_1 == type_2:
    #     type_2 = get_random_type_id(owner_client, board_with_tasks, main_space)

    type_1 = '691dc2b08b5dc0d953494916'
    type_2 = '691dc2b08b5dc0d953494915'

    with allure.step("1. Добавляем первый тип -> ожидаем TASK_TYPE_ADDED"):
        owner_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                types=[type_1]
            )
        )

        assert_history_event_exists(
            client=owner_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_TYPE_ADDED",
            expected_data={"addedTypes": "Orange"}
        )

    with allure.step("2. Добавляем второй тип к существующему -> ожидаем TASK_TYPE_ADDED"):
        owner_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                types=[type_1, type_2]
            )
        )

        assert_history_event_exists(
            client=owner_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_TYPE_ADDED",
            expected_data={"addedTypes": "Pink"}
        )

    with allure.step("3. Удаляем один тип (оставляем только type_2) -> ожидаем TASK_TYPE_REMOVED"):
        owner_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                types=[type_2]
            )
        )

        assert_history_event_exists(
            client=owner_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_TYPE_REMOVED",
            expected_data={"removedTypes": "Orange"}
        )

    with allure.step("4. Заменяем type_2 на type_1 (один ушел, один пришел) -> ожидаем генерацию ADDED и REMOVED вместо CHANGED"):
        owner_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                types=[type_1]
            )
        )

        assert_history_event_exists(
            client=owner_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_TYPE_REMOVED",
            expected_data={"removedTypes": "Pink"}
        )