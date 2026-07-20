import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_history_event_exists
from test_backend.task_service.utils import get_two_random_types

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task Types events")
def test_task_types_history_events(owner_client, main_space, temp_board_in_main, temp_task_on_temp_board):
    """
    Проверяем генерацию событий при работе с массивом типов задачи (Types):
    TASK_TYPE_ADDED -> TASK_TYPE_ADDED (еще один) -> TASK_TYPE_REMOVED -> TASK_TYPE_CHANGED
    """
    task_id = temp_task_on_temp_board

    types = get_two_random_types(owner_client, temp_board_in_main, main_space)
    type_1_id, type_1_name = types[0]
    type_2_id, type_2_name = types[1]

    with allure.step(f"1. Добавляем первый тип ({type_1_name}) -> ожидаем TASK_TYPE_ADDED"):
        owner_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                types=[type_1_id]
            )
        )

        assert_history_event_exists(
            client=owner_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_TYPE_ADDED",
            expected_data={"addedTypes": type_1_name}
        )

    with allure.step(f"2. Добавляем второй тип ({type_2_name}) к существующему -> ожидаем TASK_TYPE_ADDED"):
        owner_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                types=[type_1_id, type_2_id]
            )
        )

        assert_history_event_exists(
            client=owner_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_TYPE_ADDED",
            expected_data={"addedTypes": type_2_name}
        )

    with allure.step(f"3. Удаляем первый тип (оставляем только {type_2_name}) -> ожидаем TASK_TYPE_REMOVED"):
        owner_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                types=[type_2_id]
            )
        )

        assert_history_event_exists(
            client=owner_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_TYPE_REMOVED",
            expected_data={"removedTypes": type_1_name}
        )

    with allure.step(f"4. Заменяем {type_2_name} на {type_1_name} -> ожидаем ADDED и REMOVED"):
        owner_client.post(
            **edit_task_endpoint(
                space_id=main_space,
                task_id=task_id,
                types=[type_1_id]
            )
        )

        assert_history_event_exists(
            client=owner_client,
            space_id=main_space,
            kind="Task",
            kind_id=task_id,
            expected_event_key="TASK_TYPE_REMOVED",
            expected_data={"removedTypes": type_2_name}
        )