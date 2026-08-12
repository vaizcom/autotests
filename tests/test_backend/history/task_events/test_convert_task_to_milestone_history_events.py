import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import convert_task_to_milestone_endpoint, create_task_endpoint, \
    delete_task_endpoint
from test_backend.data.endpoints.milestone.milestones_endpoints import archive_milestone_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Convert Task to Milestone events")
def test_convert_task_to_milestone_history_events(main_client, space_for_history, board_for_history, temp_task):
    """
    Проверяем генерацию событий при конвертации задачи + сабтаски в Milestone:

    В истории нового Milestone:
      - MILESTONE_CREATED_FROM_TASK
      - TASK_ATTACHED_INTO_MILESTONE (подзадача автоматически прикреплена)

    В истории Подзадачи:
      - PARENT_TASK_CONVERTED_TO_MILESTONE
      - TASK_DETACHED_TO_PARENT (отвязка от исчезнувшей родительской задачи)
      - TASK_ATTACHED_TO_MILESTONE (привязка к новому майлстоуну)
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    parent_task_id = temp_task
    milestone_id = None

    with allure.step("Setup: создаем подзадачу для родительской задачи"):
        resp = main_client.post(
            **create_task_endpoint(
                space_id=space_id, board=board_id,
                name="Subtask for conversion test", parent_task=parent_task_id
            )
        )
        assert resp.status_code == 200, f"Ошибка создания подзадачи: {resp.text}"
        subtask_id = resp.json()['payload']['task']['_id']

    try:
        with allure.step("1. Конвертируем родительскую задачу в Майлстоун"):
            convert_resp = main_client.post(
                **convert_task_to_milestone_endpoint(space_id=space_id, task_id=parent_task_id)
            )
            assert convert_resp.status_code == 200, f"Ошибка при конвертации: {convert_resp.text}"
            milestone_id = convert_resp.json()['payload']['milestone']['_id']

        with allure.step("Проверяем событие MILESTONE_CREATED_FROM_TASK у майлстоуна: получено и содержит верные данные (_id)"):
            assert_get_history_event(
                client=main_client, space_id=space_id,
                kind="Milestone", kind_id=milestone_id,
                expected_event_key="MILESTONE_CREATED_FROM_TASK",
                expected_data={"_id": parent_task_id}
            )

        with allure.step("Проверяем каскадные события в истории подзадачи"):
            with allure.step("Проверяем событие PARENT_TASK_CONVERTED_TO_MILESTONE: получено и содержит верные данные (_id)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=subtask_id,
                    expected_event_key="PARENT_TASK_CONVERTED_TO_MILESTONE",
                    expected_data={"_id": parent_task_id}
                )

            with allure.step("Проверяем событие TASK_DETACHED_TO_PARENT: получено и содержит верные данные (_id)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=subtask_id,
                    expected_event_key="TASK_DETACHED_TO_PARENT",
                    expected_data={"_id": parent_task_id}
                )

            with allure.step("Проверяем событие TASK_ATTACHED_TO_MILESTONE: получено и содержит верные данные (milestoneId)"):
                assert_get_history_event(
                    client=main_client, space_id=space_id,
                    kind="Task", kind_id=subtask_id,
                    expected_event_key="TASK_ATTACHED_TO_MILESTONE",
                    expected_data={"milestoneId": milestone_id}
                )

        with allure.step("Проверяем событие TASK_ATTACHED_INTO_MILESTONE у майлстоуна: получено и содержит верные данные (milestoneId, taskName)"):
            assert_get_history_event(
                client=main_client, space_id=space_id,
                kind="Milestone", kind_id=milestone_id,
                expected_event_key="TASK_ATTACHED_INTO_MILESTONE",
                expected_data={"milestoneId": milestone_id, "taskName": "Subtask for conversion test"},
            )

    finally:
        with allure.step("Teardown: удаляем подзадачу и архивируем майлстоун"):
            main_client.post(**delete_task_endpoint(space_id=space_id, task_id=subtask_id))
            if milestone_id:
                main_client.post(**archive_milestone_endpoint(space_id=space_id, milestone_id=milestone_id))
