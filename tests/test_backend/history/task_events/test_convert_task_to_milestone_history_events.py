import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import convert_task_to_milestone_endpoint, create_task_endpoint, \
    delete_task_endpoint
from test_backend.data.endpoints.milestone.milestones_endpoints import archive_milestone_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Convert Task to Milestone events")
def test_convert_task_to_milestone_history_events(owner_client, main_space, main_board, temp_task):
    """
    Проверяем генерацию событий при конвертации задачи в Milestone:
    MILESTONE_CREATED_FROM_TASK (в истории нового майлстоуна)
    PARENT_TASK_CONVERTED_TO_MILESTONE (в истории подзадачи)
    """
    parent_task_id = temp_task
    milestone_id = None

    with allure.step("Setup: Создаем подзадачу для родительской задачи"):
        resp = owner_client.post(
            **create_task_endpoint(
                space_id=main_space,
                board=main_board,
                name="Subtask for conversion test",
                parent_task=parent_task_id
            )
        )
        assert resp.status_code == 200, f"Ошибка создания подзадачи: {resp.text}"
        subtask_id = resp.json()['payload']['task']['_id']

    try:
        with allure.step("1. Конвертируем родительскую задачу в Майлстоун"):
            convert_resp = owner_client.post(
                **convert_task_to_milestone_endpoint(
                    space_id=main_space,
                    task_id=parent_task_id
                )
            )
            assert convert_resp.status_code == 200, f"Ошибка при конвертации: {convert_resp.text}"

            # Получаем ID созданного майлстоуна
            milestone_id = convert_resp.json()['payload']['milestone']['_id']

        with allure.step("1.1 Проверяем историю нового Майлстоуна -> ожидаем MILESTONE_CREATED_FROM_TASK"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Milestone",
                kind_id=milestone_id,
                expected_event_key="MILESTONE_CREATED_FROM_TASK",
                expected_data={"_id": parent_task_id}
            )

        with allure.step("1.2 Проверяем каскадные события в истории Подзадачи"):
            with allure.step("A) Задача узнала о конвертации родителя"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=subtask_id,
                    expected_event_key="PARENT_TASK_CONVERTED_TO_MILESTONE",
                    expected_data={"_id": parent_task_id}
                )

            with allure.step("B) Задача была автоматически отвязана от старого родителя"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=subtask_id,
                    expected_event_key="TASK_DETACHED_TO_PARENT",
                    expected_data={"_id": parent_task_id}
                )

            with allure.step("C) Задача была автоматически привязана к новому майлстоуну"):
                assert_history_event_exists(
                    client=owner_client,
                    space_id=main_space,
                    kind="Task",
                    kind_id=subtask_id,
                    expected_event_key="TASK_ATTACHED_TO_MILESTONE",
                    # Привязка к майлстоуну пишется с указанием ID майлстоуна
                    # (как мы видели в тесте `test_task_milestones_history_events`)
                    expected_data={"_id": milestone_id}
                )

        with allure.step("1.3 Проверяем каскадное событие в самом Майлстоуне (что подзадача к нему прикрепилась)"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Milestone",
                kind_id=milestone_id,
                expected_event_key="TASK_ATTACHED_INTO_MILESTONE",
                # В майлстоуне должен быть записан ID подзадачи, которая стала его частью
                expected_data={"_id": subtask_id}
            )

    finally:
        with allure.step("Teardown: Удаляем подзадачу и архивируем майлстоун"):
            owner_client.post(**delete_task_endpoint(space_id=main_space, task_id=subtask_id))
            if milestone_id:
                owner_client.post(**archive_milestone_endpoint(space_id=main_space, milestone_id=milestone_id))