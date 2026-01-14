import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint, edit_task_endpoint
from test_backend.data.endpoints.milestone.milestones_endpoints import get_milestone_endpoint

# ID задачи из условия
TASK_ID = "696753109ee20737dcac9769"


def test_milestone_counters_update_on_task_completion(owner_client, main_space):
    """
    Проверяет сценарий на конкретной задаче (ID: 696753109ee20737dcac9769):
    1. Через GetTask узнаем текущие milestones и статус задачи.
    2. Через get_milestone_endpoint получаем исходные значения total и completed.
    3. Меняем статус задачи на противоположный.
    4. Проверяем, что total не изменился, а completed изменился на 1.

    5. Возвращаем статус обратно (Teardown).
    """

    # 1. Через GetTask узнаем текущие milestones и статус задачи.
    resp_get_task = owner_client.post(**get_task_endpoint(slug_id=TASK_ID, space_id=main_space))
    assert resp_get_task.status_code == 200
    task_data = resp_get_task.json()["payload"]["task"]

    # Предполагаем, что completed и milestones находятся в корне ответа для задачи (как в предыдущих итерациях)
    initial_completed_status = task_data.get("completed", False)
    milestone_ids = task_data.get("milestones", [])

    assert milestone_ids, f"У задачи {TASK_ID} должны быть привязаны майлстоуны для этого теста"

    # 2. Через get_milestone_endpoint получаем исходные счетчики.
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
        # 3. Меняем статус задачи на противоположный.
        resp_edit = owner_client.post(**edit_task_endpoint(
            space_id=main_space,
            task_id=TASK_ID,
            completed=new_completed_status
        ))
        assert resp_edit.status_code == 200

        # 4. Проверяем, что счетчики изменились корректно.
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

    finally:
        # 5. Возвращаем статус обратно (Teardown).
        owner_client.post(**edit_task_endpoint(
            space_id=main_space,
            task_id=TASK_ID,
            completed=initial_completed_status
        ))