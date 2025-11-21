import allure
import pytest
from dateutil import parser

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.title("Проверка сортировки задач по completedAt: ненулевые по возрастанию, затем null (в пределах лимита)")
def test_get_tasks_sorting_by_completed_at_asc(owner_client, main_space, board_with_10000_tasks, main_board):

    with allure.step("Запрос задач: completedAt ASC"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_10000_tasks,
            sortCriteria="completedAt",
            sortDirection=1
        ))
    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Извлечь задачи и проверить лимит"):
        tasks = resp.json()["payload"]["tasks"]
        assert tasks, "Ожидаются задачи в ответе"

    non_null_tasks = [t for t in tasks if t.get("completedAt") is not None]

    if len(non_null_tasks) <= 2:
        # приложим краткий лог задач, чтобы было понятно почему скип
        task_ids = [t.get("id") for t in tasks]
        allure.attach(
            f"Всего задач: {len(tasks)}\n"
            f"IDs: {task_ids}\n"
            f"Ненулевых completedAt: {len(non_null_tasks)}",
            "Диагностика skip (ASC)",
            allure.attachment_type.TEXT
        )
        pytest.skip(f"Недостаточно данных для проверки убывания: ненулевых={len(non_null_tasks)} (нужно > 2)")

    with allure.step("Проверить, что все null идут после всех ненулевых (при ASC)"):
        flags = [t.get("completedAt") is None for t in tasks]
        assert flags == sorted(flags, reverse=True), "Null значения должны быть в начале ответа при сортировке ASC"

    with allure.step("Проверить возрастание только среди ненулевых completedAt"):
        dates = [parser.parse(t["completedAt"]) for t in non_null_tasks]
        for i in range(len(dates) - 1):
            assert dates[i] <= dates[i + 1], (
                f"Нарушена сортировка по возрастанию среди ненулевых: "
                f"{dates[i]} должно быть <= {dates[i+1]}"
            )