import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import toggle_task_connector_endpoint, create_task_endpoint, \
    delete_task_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

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
    owner_client, main_space, board_with_tasks, temp_task_on_board_with_tasks,
    direction, main_task_expected_added, main_task_expected_removed,
    connector_task_expected_added, connector_task_expected_removed
):
    """
    Проверяем генерацию событий при установке зависимостей между задачами
    в обоих направлениях ('blockers' и 'blocking').
    """
    allure.dynamic.title(f"events: {direction} task connectors Blockers & Dependents (added/removed) ")

    main_task_id = temp_task_on_board_with_tasks

    with allure.step("Setup: Создана основная задача, создаем вторую задачу (connector_task)"):
        resp = owner_client.post(
            **create_task_endpoint(
                space_id=main_space,
                board=board_with_tasks,
                name=f"Connector task for direction {direction}"
            )
        )
        assert resp.status_code == 200
        connector_task_id = resp.json()['payload']['task']['_id']

    try:
        with allure.step(f"1. Устанавливаем связь в направлении '{direction}' -> ожидаем ADDED"):
            toggle_resp = owner_client.post(
                **toggle_task_connector_endpoint(
                    space_id=main_space,
                    task_id=main_task_id,
                    direction=direction,
                    task_connector_id=connector_task_id
                )
            )
            assert toggle_resp.status_code == 200, f"Ошибка при установке связи: {toggle_resp.text}"

            with allure.step(f"1.1 Проверяем историю основной задачи -> ожидаем {main_task_expected_added}"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=main_task_id,
                    expected_event_key=main_task_expected_added,
                    expected_data={"_id": connector_task_id}
                )

            with allure.step(f"1.2 Проверяем историю второй задачи -> ожидаем {connector_task_expected_added}"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=connector_task_id,
                    expected_event_key=connector_task_expected_added,
                    expected_data={"_id": main_task_id}
                )

        with allure.step(f"2. Снимаем связь '{direction}' (повторный Toggle) -> ожидаем REMOVED"):
            toggle_resp_remove = owner_client.post(
                **toggle_task_connector_endpoint(
                    space_id=main_space,
                    task_id=main_task_id,
                    direction=direction,
                    task_connector_id=connector_task_id
                )
            )
            assert toggle_resp_remove.status_code == 200, f"Ошибка при снятии связи: {toggle_resp_remove.text}"

            with allure.step(f"2.1 Проверяем историю основной задачи -> ожидаем {main_task_expected_removed}"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=main_task_id,
                    expected_event_key=main_task_expected_removed,
                    expected_data={"_id": connector_task_id}
                )

            with allure.step(f"2.2 Проверяем историю второй задачи -> ожидаем {connector_task_expected_removed}"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=connector_task_id,
                    expected_event_key=connector_task_expected_removed,
                    expected_data={"_id": main_task_id}
                )

    finally:
        with allure.step("Teardown: Удаляем задачу-коннектор"):
            owner_client.post(
                **delete_task_endpoint(
                    space_id=main_space,
                    task_id=connector_task_id
                )
            )