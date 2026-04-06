import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import toggle_milestone_endpoint
from tests.test_backend.data.endpoints.History.history_utils import assert_history_event_exists

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task & Milestones Attach/Detach events")
def test_task_milestones_history_events(owner_client, main_space, temp_task, temp_milestone):
    """
    Проверяем генерацию событий при привязке и отвязке задачи к Milestones.
    События в истории Задачи (kind="Task"):
      - TASK_ATTACHED_TO_MILESTONE
      - TASK_DETACHED_TO_MILESTONE
    События в истории Майлстоуна (kind="Milestone"):
      - TASK_ATTACHED_INTO_MILESTONE
      - TASK_DETACHED_INTO_MILESTONE
    """
    task_id = temp_task
    milestone_id = temp_milestone

    with allure.step("1. Привязываем задачу к майлстоуну (ToggleMilestone)"):
        resp_attach = owner_client.post(
            **toggle_milestone_endpoint(
                space_id=main_space,
                task_id=task_id,
                milestone_ids=[milestone_id]  # Передаем массив с ID майлстоуна (добавляем)
            )
        )
        assert resp_attach.status_code == 200, f"Ошибка привязки майлстоуна: {resp_attach.text}"

        with allure.step("1.1 Проверяем историю Задачи -> ожидаем TASK_ATTACHED_TO_MILESTONE"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_ATTACHED_TO_MILESTONE",
                # В истории задачи ожидаем увидеть ID привязанного майлстоуна
                expected_data={"_id": milestone_id}
            )

        with allure.step("1.2 Проверяем историю Майлстоуна -> ожидаем TASK_ATTACHED_INTO_MILESTONE"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Milestone",  # Запрашиваем историю Майлстоуна!
                kind_id=milestone_id,
                expected_event_key="TASK_ATTACHED_INTO_MILESTONE",
                # В истории майлстоуна ожидаем увидеть ID привязанной задачи
                expected_data={"_id": task_id}
            )

    with allure.step("2. Отвязываем задачу (повторно передаем тот же ID для toggle)"):
        resp_detach = owner_client.post(
            **toggle_milestone_endpoint(
                space_id=main_space,
                task_id=task_id,
                milestone_ids=[milestone_id]  # Тот же ID снимет привязку (toggle)
            )
        )
        assert resp_detach.status_code == 200, f"Ошибка отвязки майлстоуна: {resp_detach.text}"

        with allure.step("2.1 Проверяем историю Задачи -> ожидаем TASK_DETACHED_TO_MILESTONE"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Task",
                kind_id=task_id,
                expected_event_key="TASK_DETACHED_TO_MILESTONE",
                expected_data={"_id": milestone_id}
            )

        with allure.step("2.2 Проверяем историю Майлстоуна -> ожидаем TASK_DETACHED_INTO_MILESTONE"):
            assert_history_event_exists(
                client=owner_client,
                space_id=main_space,
                kind="Milestone",  # Запрашиваем историю Майлстоуна!
                kind_id=milestone_id,
                expected_event_key="TASK_DETACHED_INTO_MILESTONE",
                expected_data={"_id": task_id}
            )