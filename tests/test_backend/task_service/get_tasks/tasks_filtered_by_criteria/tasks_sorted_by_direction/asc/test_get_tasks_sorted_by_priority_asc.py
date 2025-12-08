import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("asc")
@allure.title("GetTasks: проверка сортировки по priority (возрастание)")
def test_get_tasks_sorted_by_priority_asc(owner_client, main_space, board_with_tasks):
    """
    Проверяет, что при сортировке по 'priority' в возрастающем порядке,
    задачи действительно отсортированы корректно.
    """
    with allure.step("Запрашиваем задачи, отсортированные по priority (возрастание)"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            sortCriteria="priority",
            sortDirection=1,  # Возрастающий порядок
        ))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

    if not tasks:
        allure.attach("Пустая выборка", "Нет задач для проверки сортировки по priority", allure.attachment_type.TEXT)
        pytest.skip("Нет задач для проверки сортировки по priority")

    if len(tasks) < 2:
        allure.attach("Недостаточно задач", "Для проверки сортировки требуется как минимум 2 задачи.",
                      allure.attachment_type.TEXT)
        pytest.skip("Недостаточно задач для проверки сортировки")

    with allure.step("Проверяем, что задачи отсортированы по priority в возрастающем порядке"):
        for i in range(len(tasks) - 1):
            current_priority = tasks[i].get("priority")
            next_priority = tasks[i + 1].get("priority")

            assert current_priority <= next_priority, \
                f"Нарушение сортировки по priority (возрастание): " \
                f"Задача {tasks[i].get('_id')} ({current_priority}) " \
                f"идет после задачи {tasks[i + 1].get('_id')} ({next_priority})"