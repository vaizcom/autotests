import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.sub_suite("Sort by Direction ASC")
@allure.title("GetTasks archived_at_asc: проверка сортировки по archivedAt при archived=true (возрастание)")
def test_get_tasks_sorted_by_archived_at_asc(owner_client, main_space, board_with_10000_tasks):
    """
    Проверяет, что при archived=true и сортировке по archivedAt в возрастающем порядке,
    задачи действительно отсортированы корректно.
    """
    with allure.step("Запрашиваем задачи с archived=true, отсортированные по archivedAt (возрастание)"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            archived=True,
            limit=50,  # Запрашиваем достаточно задач для проверки сортировки
            board=board_with_10000_tasks,
            sortCriteria="archivedAt",
            sortDirection=1  # Возрастающий порядок
        ))
        resp.raise_for_status()
        tasks = resp.json()["payload"].get("tasks", [])

    if not tasks:
        allure.attach("Пустая выборка", "Нет задач для проверки сортировки при archived=true", allure.attachment_type.TEXT)
        pytest.skip("Нет задач для проверки сортировки при archived=true")

    # Отфильтровываем только те задачи, у которых archivedAt является непустой строкой (т.е. они действительно архивные)
    archived_tasks = [t for t in tasks if isinstance(t.get("archivedAt"), str) and t.get("archivedAt").strip()]

    if len(archived_tasks) < 2:
        allure.attach("Недостаточно архивных задач", "Для проверки сортировки требуется как минимум 2 архивные задачи.",
                      allure.attachment_type.TEXT)
        pytest.skip("Недостаточно архивных задач для проверки сортировки")

    with allure.step("Проверяем, что задачи отсортированы по archivedAt в возрастающем порядке"):
        for i in range(len(archived_tasks) - 1):
            current_archived_at = archived_tasks[i].get("archivedAt")
            next_archived_at = archived_tasks[i + 1].get("archivedAt")

            assert isinstance(current_archived_at, str) and current_archived_at.strip(), \
                f"Задача {archived_tasks[i].get('_id')} имеет некорректный archivedAt: {current_archived_at!r}"
            assert isinstance(next_archived_at, str) and next_archived_at.strip(), \
                f"Задача {archived_tasks[i + 1].get('_id')} имеет некорректный archivedAt: {next_archived_at!r}"

            # Сравниваем строковые представления дат (ISO 8601 даты могут быть сравнимы лексикографически)
            assert current_archived_at <= next_archived_at, \
                f"Нарушение сортировки по archivedAt (возрастание): " \
                f"Задача {archived_tasks[i].get('_id')} ({current_archived_at}) " \
                f"идет после задачи {archived_tasks[i + 1].get('_id')} ({next_archived_at})"