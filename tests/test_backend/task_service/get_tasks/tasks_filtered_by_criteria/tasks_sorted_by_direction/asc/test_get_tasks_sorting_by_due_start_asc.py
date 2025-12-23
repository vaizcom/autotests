import allure
import pytest
from dateutil import parser

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.sub_suite("Sort by Direction ASC")
@allure.title("GetTasks dueStart_asc: Проверка сортировки задач по dueStart: ненулевые по убыванию, затем null (в пределах лимита)")
def test_get_tasks_sorting_by_due_start_asc(owner_client, main_space, board_with_10000_tasks, main_board):

    with allure.step("Запрос задач: dueStart ASC"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_10000_tasks,
            sortCriteria="dueStart",
            sortDirection=1
        ))
    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Извлечь задачи и проверить лимит"):
        tasks = resp.json()["payload"]["tasks"]
        assert tasks, "Ожидаются задачи в ответе"

    non_null_tasks = [t for t in tasks if t.get("dueStart") is not None]

    if len(non_null_tasks) <= 2:
        task_ids = [t.get("id") for t in tasks]
        allure.attach(
            f"Всего задач: {len(tasks)}\n"
            f"IDs: {task_ids}\n"
            f"Ненулевых dueStart: {len(non_null_tasks)}",
            "Диагностика skip (ASC)",
            allure.attachment_type.TEXT
        )
        pytest.skip(f"Недостаточно данных для проверки убывания: ненулевых={len(non_null_tasks)} (нужно > 2)")

    with allure.step("Проверить, что все null идут после всех ненулевых (при ASC)"):
        flags = [t.get("dueStart") is None for t in tasks]
        assert flags == sorted(flags, reverse=True), "Null значения должны быть в начале ответа при сортировке ASC"

    with allure.step("Проверить возрастание только среди ненулевых dueStart"):
        dates = [parser.parse(t["dueStart"]) for t in non_null_tasks[:20]]
        for i in range(len(dates) - 1):
            assert dates[i] <= dates[i + 1], (
                f"Нарушена сортировка по возрастанию среди ненулевых: "
                f"{dates[i]} должно быть <= {dates[i+1]}"
            )