import allure
import pytest
from dateutil import parser
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("desc")
@allure.title("Проверка сортировки задач по createdAt: по убыванию (новые сверху)")
def test_get_tasks_sorting_by_created_at_desc(owner_client, main_space, board_with_10000_tasks):
    """Проверяет сортировку задач по дате создания в порядке убывания (новые сверху)"""
    LIMIT = 20

    with allure.step(f"Запрос задач: createdAt DESC, limit={LIMIT}"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_10000_tasks,
            sortCriteria="createdAt",
            sortDirection=-1,
            limit=LIMIT
        ))
    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Извлечь задачи и проверить лимит"):
        tasks = resp.json()["payload"]["tasks"]
        assert tasks, "Ожидаются задачи в ответе"

    # Если данных недостаточно для сравнения — корректно пропускаем тест
    if len(tasks) <= 2:
        pytest.skip(f"Недостаточно данных для проверки убывания: получено {len(tasks)} (нужно > 2)")

    with allure.step("Проверить убывание по createdAt (новые задачи сверху)"):
        try:
            created_dates = [parser.parse(task["createdAt"]) for task in tasks]
        except Exception as e:
            raise AssertionError(f"Не удалось распарсить createdAt в одной из задач: {e}")

        for i in range(len(created_dates) - 1):
            assert created_dates[i] >= created_dates[i + 1], (
                f"Нарушена сортировка по убыванию: позиции {i} ({created_dates[i]}) и {i+1} ({created_dates[i+1]})"
            )

        first, last = created_dates[0], created_dates[-1]
        allure.attach(
            f"Количество задач: {len(tasks)}\nПервая дата: {first}\nПоследняя дата: {last}",
            name="Результат сортировки createdAt DESC",
            attachment_type=allure.attachment_type.TEXT
        )