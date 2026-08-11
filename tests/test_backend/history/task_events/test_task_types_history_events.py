import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint, create_task_endpoint, delete_task_endpoint
from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.History.history_utils import (
    assert_get_history_event,
    assert_get_history_no_event,
)
from test_backend.task_service.utils import get_two_random_types
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response

pytestmark = [pytest.mark.backend]

_TASK_NAME = "Temp task for history events"


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task Types events: TASK_TYPE_ADDED & TASK_TYPE_REMOVED")
def test_task_types_history_events(main_client, space_for_history, board_for_history, temp_task):
    """
    Проверяем генерацию событий при работе с массивом типов задачи (Types):
    TASK_TYPE_ADDED -> TASK_TYPE_ADDED (еще один) -> TASK_TYPE_REMOVED -> TASK_TYPE_CHANGED
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    task_id = temp_task

    types = get_two_random_types(main_client, board_id, space_id)
    type_1_id, type_1_name = types[0]
    type_2_id, type_2_name = types[1]

    with allure.step(f"1. Добавляем первый тип ({type_1_name})"):
        main_client.post(
            **edit_task_endpoint(space_id=space_id, task_id=task_id, types=[type_1_id])
        )

        with allure.step("Проверяем событие TASK_TYPE_ADDED: получено и содержит верные данные (_id, name, addedTypes)"):
            assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_TYPE_ADDED",
                expected_data={"_id": task_id, "name": _TASK_NAME, "addedTypes": type_1_name},
            )

    with allure.step(f"2. Добавляем второй тип ({type_2_name}) к существующему"):
        main_client.post(
            **edit_task_endpoint(space_id=space_id, task_id=task_id, types=[type_1_id, type_2_id])
        )

        with allure.step("Проверяем событие TASK_TYPE_ADDED: получено и содержит верные данные (_id, name, addedTypes)"):
            assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_TYPE_ADDED",
                expected_data={"_id": task_id, "name": _TASK_NAME, "addedTypes": type_2_name},
            )

    with allure.step(f"3. Удаляем первый тип (оставляем только {type_2_name})"):
        main_client.post(
            **edit_task_endpoint(space_id=space_id, task_id=task_id, types=[type_2_id])
        )

        with allure.step("Проверяем событие TASK_TYPE_REMOVED: получено и содержит верные данные (_id, name, removedTypes)"):
            assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_TYPE_REMOVED",
                expected_data={"_id": task_id, "name": _TASK_NAME, "removedTypes": type_1_name},
            )

    with allure.step(f"4. Заменяем {type_2_name} на {type_1_name}"):
        main_client.post(
            **edit_task_endpoint(space_id=space_id, task_id=task_id, types=[type_1_id])
        )

        with allure.step("Проверяем событие TASK_TYPE_REMOVED: получено и содержит верные данные (_id, name, removedTypes)"):
            assert_get_history_event(
                client=main_client,
                space_id=space_id,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_TYPE_REMOVED",
                expected_data={"_id": task_id, "name": _TASK_NAME, "removedTypes": type_2_name},
            )


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task Types events via MultipleEditTasks: TASK_TYPE_ADDED (mixed) -> TASK_TYPE_REMOVED")
def test_task_types_history_events_multiaction(main_client, space_for_history, board_for_history):
    """
    Проверяем, что MultipleEditTasks генерирует history-события только для задач,
    которые реально изменились, и не генерирует для пропущенных.
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]

    types = get_two_random_types(main_client, board_id, space_id)
    type_1_id, type_1_name = types[0]

    created_ids = []
    with allure.step("Создаём задачу_А без типа и задачу_Б с типом"):
        resp = main_client.post(**create_task_endpoint(
            space_id=space_id, board=board_id, name="task-A-without-type",
        ))
        assert resp.status_code == 200, resp.text
        task_a_id = resp.json()["payload"]["task"]["_id"]
        created_ids.append(task_a_id)

        resp = main_client.post(**create_task_endpoint(
            space_id=space_id, board=board_id, name="task-B-with-type", types=[type_1_id],
        ))
        assert resp.status_code == 200, resp.text
        task_b_id = resp.json()["payload"]["task"]["_id"]
        created_ids.append(task_b_id)

    try:
        with allure.step(f"Добавляем тип ({type_1_name}) на обе задачи"):
            resp = main_client.post(**multiple_edit_tasks_endpoint(
                space_id=space_id,
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

        with allure.step("Задача_А изменилась"):
            with allure.step("Проверяем событие TASK_TYPE_ADDED: получено и содержит верные данные (_id, name, addedTypes)"):
                assert_get_history_event(
                    client=main_client,
                    space_id=space_id,
                    kind="Task",
                    kind_id=task_a_id,
                    expected_event_key="TASK_TYPE_ADDED",
                    expected_data={"_id": task_a_id, "name": "task-A-without-type", "addedTypes": type_1_name},
                )

        with allure.step("Задача_Б пропущена"):
            with allure.step("Проверяем через GetHistory что событие TASK_TYPE_ADDED отсутствует"):
                assert_get_history_no_event(
                    client=main_client,
                    space_id=space_id,
                    kind="Task",
                    kind_id=task_b_id,
                    expected_event_key="TASK_TYPE_ADDED",
                    expected_data={"addedTypes": type_1_name},
                )

        with allure.step(f"Удаляем тип ({type_1_name}) с обеих задач"):
            resp = main_client.post(**multiple_edit_tasks_endpoint(
                space_id=space_id,
                tasks_ids=[task_a_id, task_b_id],
                types=[type_1_id, "remove"],
            ))
            assert resp.status_code == 200, resp.text

        with allure.step("Обе задачи изменились"):
            task_names = {task_a_id: "task-A-without-type", task_b_id: "task-B-with-type"}
            for tid in [task_a_id, task_b_id]:
                with allure.step(f"Проверяем событие TASK_TYPE_REMOVED: получено и содержит верные данные (_id, name, removedTypes) для задачи {tid}"):
                    assert_get_history_event(
                        client=main_client,
                        space_id=space_id,
                        kind="Task",
                        kind_id=tid,
                        expected_event_key="TASK_TYPE_REMOVED",
                        expected_data={"_id": tid, "name": task_names[tid], "removedTypes": type_1_name},
                    )
    finally:
        with allure.step("Teardown: удаляем созданные задачи"):
            for tid in created_ids:
                main_client.post(**delete_task_endpoint(task_id=tid, space_id=space_id))
