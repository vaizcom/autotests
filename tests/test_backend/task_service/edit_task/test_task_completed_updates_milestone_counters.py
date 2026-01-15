import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint, edit_task_endpoint
from test_backend.data.endpoints.milestone.milestones_endpoints import get_milestone_endpoint

pytestmark = [pytest.mark.backend]

# ID задачи в которой есть два майлстоуна
TASK_ID = "696753109ee20737dcac9769"

@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Completed edit Task in Milestones counters")
@allure.title("Проверка обновления счетчиков майлстоуна при изменении Completed задачи")
def test_milestone_counters_update_on_task_completion1(owner_client, main_space):
    """
        Тест проверяет корректность пересчета счетчиков (completed, total) в майлстоунах
        при переключении статуса выполнения задачи туда и обратно.
        """

    with allure.step("1. Получение списка майлстоунов и текущего статуса задачи через GetTask"):
        resp_get_task = owner_client.post(**get_task_endpoint(slug_id=TASK_ID, space_id=main_space))
        assert resp_get_task.status_code == 200
        task_data = resp_get_task.json()["payload"]["task"]

        initial_completed_status = task_data.get("completed", False)
        milestone_ids = task_data.get("milestones", [])

        assert milestone_ids, f"У задачи {TASK_ID} должны быть привязаны майлстоуны для этого теста"

    with allure.step("2. Фиксация исходных значений счетчиков (total, completed) для майлстоунов"):
        initial_stats = {}
        for ms_id in milestone_ids:
            resp_ms = owner_client.post(**get_milestone_endpoint(ms_id=ms_id, space_id=main_space))
            assert resp_ms.status_code == 200
            assert TASK_ID in resp_ms.json()["payload"]["milestone"]["tasks"]

            # Извлекаем данные по указанному пути
            ms_data = resp_ms.json()["payload"]["milestone"]
            initial_stats[ms_id] = {
                "total": ms_data["total"],
                "completed": ms_data["completed"]
            }

    # Определяем новый статус (противоположный текущему)
    new_completed_status = not initial_completed_status

    try:
        with allure.step(f"3. Смена статуса задачи на противоположный (completed={new_completed_status})"):
            resp_edit = owner_client.post(**edit_task_endpoint(
                space_id=main_space,
                task_id=TASK_ID,
                completed=new_completed_status
            ))
            assert resp_edit.status_code == 200

        with allure.step("4. Проверка: total не изменился, completed изменился ровно на 1"):
            for ms_id in milestone_ids:
                resp_ms_check = owner_client.post(**get_milestone_endpoint(ms_id=ms_id, space_id=main_space))
                assert resp_ms_check.status_code == 200

                ms_data_current = resp_ms_check.json()["payload"]["milestone"]

                current_total = ms_data_current["total"]
                current_completed = ms_data_current["completed"]

                prev_total = initial_stats[ms_id]["total"]
                prev_completed = initial_stats[ms_id]["completed"]

                # Total — общее количество задач, оно не должно меняться при смене статуса выполнения
                assert current_total == prev_total, \
                    f"Milestone {ms_id}: счетчик total не должен меняться"

                if new_completed_status:
                    # Задача стала выполненной (True): счетчик completed должен увеличиться
                    assert current_completed == prev_completed + 1, \
                        f"Milestone {ms_id}: счетчик completed должен увеличиться на 1"
                else:
                    # Задача стала невыполненной (False): счетчик completed должен уменьшиться
                    assert current_completed == prev_completed - 1, \
                        f"Milestone {ms_id}: счетчик completed должен уменьшиться на 1"

        with allure.step("5. Возврат статуса задачи в исходное (False) и проверка восстановления счетчиков"):
            resp_revert = owner_client.post(**edit_task_endpoint(
                space_id=main_space,
                task_id=TASK_ID,
                completed=initial_completed_status
            ))
            assert resp_revert.status_code == 200

            for ms_id in milestone_ids:
                resp_ms_back = owner_client.post(**get_milestone_endpoint(ms_id=ms_id, space_id=main_space))
                assert resp_ms_back.status_code == 200

                ms_data_back = resp_ms_back.json()["payload"]["milestone"]
                current_completed_back = ms_data_back["completed"]
                initial_val = initial_stats[ms_id]["completed"]

                assert current_completed_back == initial_val, \
                    f"Milestone {ms_id}: после возврата статуса счетчик completed должен вернуться к {initial_val}"

    finally:
        # Teardown (на случай падения assert'ов внутри try)
        owner_client.post(**edit_task_endpoint(
            space_id=main_space,
            task_id=TASK_ID,
            completed=initial_completed_status
        ))