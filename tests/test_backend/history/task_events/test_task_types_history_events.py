import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint, create_task_endpoint, delete_task_endpoint
from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.History.history_utils import (
    assert_history_event_exists,
    assert_history_event_not_exists,
)
from test_backend.task_service.utils import get_two_random_types
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response

pytestmark = [pytest.mark.backend, pytest.mark.skip(reason="APP-5670: рефакторинг history")]


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


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task Types events via MultipleEditTasks: TASK_TYPE_ADDED (mixed) -> TASK_TYPE_REMOVED")
def test_task_types_history_events_multiaction(owner_client, main_space, temp_board_in_main):
    """
    Проверяем, что MultipleEditTasks генерирует history-события только для задач,
    которые реально изменились, и не генерирует для пропущенных.

    Сценарий:
    1. Создаём задачу_А (без типа) и задачу_Б (уже с типом).
    2. Добавляем тип на обе → задача_А изменилась, задача_Б пропущена (тип уже есть).
       - У задачи_А должно появиться событие TASK_TYPE_ADDED.
       - У задачи_Б событие НЕ должно появиться.
    3. Удаляем тип с обеих (теперь обе с типом) → обе изменились.
       - У обеих должно появиться событие TASK_TYPE_REMOVED.
    """
    import time as _time

    types = get_two_random_types(owner_client, temp_board_in_main, main_space)
    type_1_id, type_1_name = types[0]

    created_ids = []
    with allure.step("Создаём задачу_А без типа и задачу_Б с типом"):
        resp = owner_client.post(**create_task_endpoint(
            space_id=main_space, board=temp_board_in_main,
            name="task-A-without-type",
        ))
        assert resp.status_code == 200, resp.text
        task_a_id = resp.json()["payload"]["task"]["_id"]
        created_ids.append(task_a_id)

        resp = owner_client.post(**create_task_endpoint(
            space_id=main_space, board=temp_board_in_main,
            name="task-B-with-type", types=[type_1_id],
        ))
        assert resp.status_code == 200, resp.text
        task_b_id = resp.json()["payload"]["task"]["_id"]
        created_ids.append(task_b_id)

    try:
        with allure.step("Запоминаем timestamp перед добавлением типа"):
            before_add_ts = _time.time()

        with allure.step(f"Добавляем тип ({type_1_name}) на обе задачи"):
            resp = owner_client.post(**multiple_edit_tasks_endpoint(
                space_id=main_space,
                tasks_ids=[task_a_id, task_b_id],
                types=[type_1_id, "add"],
            ))
            assert resp.status_code == 200, resp.text
            payload = assert_multiaction_response(resp)
            assert task_a_id in payload["success"], (
                f"Задача_А должна быть изменена (success): {payload}"
            )
            assert task_b_id in payload["skipped"], (
                f"Задача_Б должна быть пропущена (тип уже есть): {payload}"
            )

        with allure.step("Задача_А изменилась → событие TASK_TYPE_ADDED есть"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Task",
                kind_id=task_a_id,
                expected_event_key="TASK_TYPE_ADDED",
                expected_data={"addedTypes": type_1_name}
            )

        with allure.step("Задача_Б пропущена → событие TASK_TYPE_ADDED отсутствует"):
            assert_history_event_not_exists(
                client=owner_client,
                space_id=main_space,
                kind="Task",
                kind_id=task_b_id,
                expected_event_key="TASK_TYPE_ADDED",
                expected_data={"addedTypes": type_1_name},
                after_ts=before_add_ts,
            )

        with allure.step(f"Удаляем тип ({type_1_name}) с обеих задач"):
            resp = owner_client.post(**multiple_edit_tasks_endpoint(
                space_id=main_space,
                tasks_ids=[task_a_id, task_b_id],
                types=[type_1_id, "remove"],
            ))
            assert resp.status_code == 200, resp.text

        with allure.step("Обе задачи изменились → событие TASK_TYPE_REMOVED у обеих"):
            for tid in [task_a_id, task_b_id]:
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=tid,
                    expected_event_key="TASK_TYPE_REMOVED",
                    expected_data={"removedTypes": type_1_name}
                )
    finally:
        with allure.step("Teardown: удаляем созданные задачи"):
            for tid in created_ids:
                owner_client.post(**delete_task_endpoint(task_id=tid, space_id=main_space))