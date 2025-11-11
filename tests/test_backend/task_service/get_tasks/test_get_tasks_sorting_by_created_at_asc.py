
import allure
import pytest
from dateutil import parser

from core.auth import reset_token_cache
from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.title("Проверка сортировки задач по дате создания (по возрастанию)")
def test_get_tasks_sorting_by_created_at_asc(owner_client, main_space, board_with_tasks):
    """Проверяет сортировку задач по дате создания в порядке возрастания (старые сверху)"""

    with allure.step("Выполнить запрос с сортировкой по createdAt ASC и лимитом 10"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            sortCriteria="createdAt",
            sortDirection=1,
            limit=10
        ))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Проверить сортировку по возрастанию (старые задачи сверху)"):
        tasks = resp.json()["payload"]["tasks"]

        assert len(tasks) <= 10, "Количество задач не должно превышать лимит"

        if len(tasks) > 1:
            created_dates = [parser.parse(task["createdAt"]) for task in tasks]

            # Проверяем сортировку по возрастанию (каждая следующая дата >= предыдущей)
            for i in range(len(created_dates) - 1):
                assert created_dates[i] <= created_dates[i + 1], \
                    f"Нарушена сортировка по возрастанию: {created_dates[i]} должна быть <= {created_dates[i + 1]}"

            allure.attach(
                f"Количество задач: {len(tasks)}\nПервая задача: {created_dates[0]}\nПоследняя задача: {created_dates[-1]}",
                "Результат сортировки",
                allure.attachment_type.TEXT
            )

@allure.title("Проверка сортировки по умолчанию (должна быть по возрастанию)")
def test_get_tasks_default_sorting(owner_client, main_space, board_with_tasks):
    """Проверяет что без указания sortDirection сортировка происходит по возрастанию"""

    with allure.step("Выполнить запрос с sortCriteria без sortDirection"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_tasks,
            sortCriteria="createdAt",
            limit=15
            # sortDirection НЕ указываем - проверяем поведение по умолчанию
        ))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Проверить что сортировка по умолчанию - по возрастанию"):
        tasks = resp.json()["payload"]["tasks"]

        assert len(tasks) <= 15, "Количество задач не должно превышать лимит"

        if len(tasks) > 1:
            created_dates = [parser.parse(task["createdAt"]) for task in tasks]

            # Проверяем что это именно сортировка по возрастанию
            for i in range(len(created_dates) - 1):
                assert created_dates[i] <= created_dates[i + 1], \
                    f"Сортировка по умолчанию должна быть по возрастанию, но {created_dates[i]} > {created_dates[i + 1]}"

            allure.attach(
                f"Сортировка по умолчанию: ПО ВОЗРАСТАНИЮ ✓\n"
                f"Количество задач: {len(tasks)}\n"
                f"Первая (самая старая) задача: {created_dates[0]}\n"
                f"Последняя (самая новая) задача: {created_dates[-1]}",
                "Результат проверки сортировки по умолчанию",
                allure.attachment_type.TEXT
            )
        else:
            allure.attach("Недостаточно задач для проверки сортировки", "Предупреждение", allure.attachment_type.TEXT)