import allure
import pytest
from dateutil import parser

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@pytest.mark.skip
@allure.title("Проверка сортировки задач по completedAt: ненулевые по убыванию, затем null (в пределах лимита)")
def test_get_tasks_sorting_by_completed_at_desc(owner_client, main_space, board_with_tasks, main_board):
    limit = 20

    with allure.step(f"Запрос задач: completedAt DESC, limit={limit}"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            sortCriteria="completedAt",
            sortDirection=-1,
            limit=limit
        ))
    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Извлечь задачи и проверить лимит"):
        tasks = resp.json()["payload"]["tasks"]
        assert tasks, "Ожидаются задачи в ответе"
        assert len(tasks) <= limit, f"Размер ответа {len(tasks)} превышает лимит {limit}"

    # Разделяем по признаку null
    non_null_tasks = [t for t in tasks if t.get("completedAt") is not None]
    null_tasks = [t for t in tasks if t.get("completedAt") is None]

    # Если данных недостаточно для сравнения — корректно пропускаем тест
    if len(non_null_tasks) <= 2:
        pytest.skip(f"Недостаточно данных для проверки убывания: ненулевых={len(non_null_tasks)} (нужно > 2)")

    with allure.step("Проверить, что все null идут после всех ненулевых"):
        flags = [t.get("completedAt") is None for t in tasks]
        # должно быть: False...False, True...True
        assert flags == sorted(flags), "Null значения должны быть только в хвосте ответа"

    with allure.step("Проверить убывание только среди ненулевых completedAt"):
        try:
            dates = [parser.parse(t["completedAt"]) for t in non_null_tasks]
        except Exception as e:
            raise AssertionError(f"Не удалось распарсить completedAt в одной из задач: {e}")

        for i in range(len(dates) - 1):
            assert dates[i] >= dates[i + 1], (
                f"Нарушена сортировка по убыванию среди ненулевых: "
                f"позиции {i} ({dates[i]}) и {i+1} ({dates[i+1]}), "
                f"taskIds: {non_null_tasks[i].get('id')} -> {non_null_tasks[i+1].get('id')}"
            )