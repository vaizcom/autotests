import allure
import pytest
from dateutil import parser

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.title("Проверка сортировки задач по дате создания (по убыванию)")
def test_get_tasks_sorting_by_created_at_desc(owner_client, main_space, board_with_tasks):
    """Проверяет сортировку задач по дате создания в порядке убывания (новые сверху)"""

    with allure.step("Выполнить запрос с сортировкой по createdAt DESC"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            sortCriteria="createdAt",
            sortDirection=-1,

        ))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Проверить сортировку по убыванию (новые задачи сверху)"):
        tasks = resp.json()["payload"]["tasks"]

        assert len(tasks) <= 50000, "Количество задач не должно превышать лимит"

        if len(tasks) > 1:
            created_dates = [parser.parse(task["createdAt"]) for task in tasks]

            # Проверяем сортировку по убыванию (каждая следующая дата <= предыдущей)
            for i in range(len(created_dates) - 1):
                assert created_dates[i] >= created_dates[i + 1], \
                    f"Нарушена сортировка по убыванию: {created_dates[i]} должна быть >= {created_dates[i + 1]}"

            allure.attach(
                f"Количество задач: {len(tasks)}\nПервая задача: {created_dates[0]}\nПоследняя задача: {created_dates[-1]}",
                "Результат сортировки",
                allure.attachment_type.TEXT
            )

