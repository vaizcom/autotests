import pytest
import allure
from datetime import datetime
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


# ===== ТЕСТЫ СОРТИРОВКИ =====

@allure.title("Проверка сортировки задач по дате создания")
def test_get_tasks_sorting_by_created_at(owner_client, manager_client, main_space, board_with_tasks, main_project):
    """Проверяет корректность сортировки задач по дате создания"""

    with allure.step("Получить список задач"):
        resp = owner_client.post(**get_tasks_endpoint(space_id=main_space, board=board_with_tasks))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Проверить сортировку по createdAt"):
        tasks = resp.json()["payload"]["tasks"]

        if len(tasks) > 1:
            created_dates = [datetime.fromisoformat(task["createdAt"].replace('Z', '+00:00')) for task in tasks]

            # Проверяем что сортировка консистентна
            is_ascending = all(created_dates[i] <= created_dates[i+1] for i in range(len(created_dates)-1))
            is_descending = all(created_dates[i] >= created_dates[i+1] for i in range(len(created_dates)-1))

            assert is_ascending or is_descending, "Задачи должны быть отсортированы по дате создания"

            sort_order = "по возрастанию" if is_ascending else "по убыванию"
            allure.attach(f"Задачи отсортированы {sort_order}", "Порядок сортировки", allure.attachment_type.TEXT)



