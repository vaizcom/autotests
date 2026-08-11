import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import toggle_milestone_endpoint
from test_backend.data.endpoints.History.history_utils import assert_get_history_event

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.title("Task & Milestones Attach/Detach events")
def test_task_milestones_history_events(main_client, space_for_history, temp_task, temp_milestone):
    """
    Проверяем генерацию событий при привязке и отвязке задачи к Milestone.
    События в истории Задачи (kind="Task"):
      - TASK_ATTACHED_TO_MILESTONE / TASK_DETACHED_TO_MILESTONE
    События в истории Майлстоуна (kind="Milestone"):
      - TASK_ATTACHED_INTO_MILESTONE / TASK_DETACHED_INTO_MILESTONE
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    milestone_id = temp_milestone

    with allure.step("1. Привязываем задачу к майлстоуну (ToggleMilestone)"):
        resp_attach = main_client.post(
            **toggle_milestone_endpoint(
                space_id=space_id, task_id=task_id, milestone_ids=[milestone_id]
            )
        )
        assert resp_attach.status_code == 200, f"Ошибка привязки майлстоуна: {resp_attach.text}"

        with allure.step("Проверяем событие TASK_ATTACHED_TO_MILESTONE у задачи: получено и содержит верные данные (milestoneId)"):
            assert_get_history_event(
                client=main_client, space_id=space_id,
                kind="Task", kind_id=task_id,
                expected_event_key="TASK_ATTACHED_TO_MILESTONE",
                expected_data={"milestoneId": milestone_id}
            )

        with allure.step("Проверяем событие TASK_ATTACHED_INTO_MILESTONE у майлстоуна: получено и содержит верные данные (milestoneId, taskName)"):
            assert_get_history_event(
                client=main_client, space_id=space_id,
                kind="Milestone", kind_id=milestone_id,
                expected_event_key="TASK_ATTACHED_INTO_MILESTONE",
                expected_data={"milestoneId": milestone_id, "taskName": "Temp task for history events"},
            )

    with allure.step("2. Отвязываем задачу (повторный toggle)"):
        resp_detach = main_client.post(
            **toggle_milestone_endpoint(
                space_id=space_id, task_id=task_id, milestone_ids=[milestone_id]
            )
        )
        assert resp_detach.status_code == 200, f"Ошибка отвязки майлстоуна: {resp_detach.text}"

        with allure.step("Проверяем событие TASK_DETACHED_TO_MILESTONE у задачи: получено и содержит верные данные (milestoneId)"):
            assert_get_history_event(
                client=main_client, space_id=space_id,
                kind="Task", kind_id=task_id,
                expected_event_key="TASK_DETACHED_TO_MILESTONE",
                expected_data={"milestoneId": milestone_id}
            )

        with allure.step("Проверяем событие TASK_DETACHED_INTO_MILESTONE у майлстоуна: получено и содержит верные данные (milestoneId, taskName)"):
            assert_get_history_event(
                client=main_client, space_id=space_id,
                kind="Milestone", kind_id=milestone_id,
                expected_event_key="TASK_DETACHED_INTO_MILESTONE",
                expected_data={"milestoneId": milestone_id, "taskName": "Temp task for history events"},
            )
