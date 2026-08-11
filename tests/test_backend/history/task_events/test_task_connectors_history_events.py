import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import toggle_task_connector_endpoint, create_task_endpoint, \
    delete_task_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@pytest.mark.parametrize(
    "direction, main_task_expected_added, main_task_expected_removed, connector_task_expected_added, connector_task_expected_removed",
    [
        (
            "blockers",
            "TASK_DEPENDENT_ADDED", "TASK_DEPENDENT_REMOVED",
            "TASK_BLOCKER_ADDED", "TASK_BLOCKER_REMOVED"
        ),
        (
            "blocking",
            "TASK_BLOCKER_ADDED", "TASK_BLOCKER_REMOVED",
            "TASK_DEPENDENT_ADDED", "TASK_DEPENDENT_REMOVED"
        )
    ],
    ids=["blockers", "blocking"]
)
def test_task_connectors_history_events(
    main_client, space_for_history, board_for_history, temp_task,
    direction, main_task_expected_added, main_task_expected_removed,
    connector_task_expected_added, connector_task_expected_removed
):
    """
    Проверяем генерацию событий при установке зависимостей между задачами
    в обоих направлениях ('blockers' и 'blocking').
    """
    allure.dynamic.title(f"{direction} task connectors: Добавление и удаление связей для '{direction}'")

    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    main_task_id = temp_task

    connector_task_name = f"Connector task for direction {direction}"
    main_task_name = "Temp task for history events"

    with allure.step("Setup: создаем вторую задачу (connector_task)"):
        resp = main_client.post(
            **create_task_endpoint(
                space_id=space_id, board=board_id,
                name=connector_task_name,
            )
        )
        assert resp.status_code == 200
        connector_task_id = resp.json()['payload']['task']['_id']

    try:
        with allure.step(f"1. Устанавливаем связь в направлении '{direction}'"):
            toggle_resp = main_client.post(
                **toggle_task_connector_endpoint(
                    space_id=space_id, task_id=main_task_id,
                    direction=direction, task_connector_id=connector_task_id
                )
            )
            assert toggle_resp.status_code == 200, f"Ошибка при установке связи: {toggle_resp.text}"

            with allure.step(f"Проверяем событие {main_task_expected_added} у основной задачи: получено и содержит верные данные (_id, name)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=main_task_id,
                    expected_event_key=main_task_expected_added,
                    expected_data={"_id": connector_task_id, "name": connector_task_name},
                )

            with allure.step(f"Проверяем событие {connector_task_expected_added} у второй задачи: получено и содержит верные данные (_id, name)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=connector_task_id,
                    expected_event_key=connector_task_expected_added,
                    expected_data={"_id": main_task_id, "name": main_task_name},
                )

        with allure.step(f"2. Снимаем связь '{direction}' (повторный Toggle)"):
            toggle_resp_remove = main_client.post(
                **toggle_task_connector_endpoint(
                    space_id=space_id, task_id=main_task_id,
                    direction=direction, task_connector_id=connector_task_id
                )
            )
            assert toggle_resp_remove.status_code == 200, f"Ошибка при снятии связи: {toggle_resp_remove.text}"

            with allure.step(f"Проверяем событие {main_task_expected_removed} у основной задачи: получено и содержит верные данные (_id, name)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=main_task_id,
                    expected_event_key=main_task_expected_removed,
                    expected_data={"_id": connector_task_id, "name": connector_task_name},
                )

            with allure.step(f"Проверяем событие {connector_task_expected_removed} у второй задачи: получено и содержит верные данные (_id, name)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=connector_task_id,
                    expected_event_key=connector_task_expected_removed,
                    expected_data={"_id": main_task_id, "name": main_task_name},
                )

    finally:
        with allure.step("Teardown: удаляем задачу-коннектор"):
            main_client.post(**delete_task_endpoint(space_id=space_id, task_id=connector_task_id))
