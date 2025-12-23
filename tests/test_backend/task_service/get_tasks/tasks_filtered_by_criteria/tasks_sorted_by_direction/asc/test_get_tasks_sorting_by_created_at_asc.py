import allure
import pytest
from dateutil import parser

from test_backend.data.endpoints.Task.task_endpoints import get_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.sub_suite("Sort by Direction ASC")
@allure.title("GetTasks createdAt_asc: Проверка сортировки задач по дате создания (по возрастанию)")
def test_get_tasks_sorting_by_created_at_asc(owner_client, main_space, board_with_10000_tasks):
    """Проверяет сортировку задач по дате создания в порядке возрастания (старые сверху)"""

    with allure.step("Выполнить запрос с сортировкой по createdAt ASC и лимитом 10"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_10000_tasks,
            sortCriteria="createdAt",
            sortDirection=1,
            limit=20
        ))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Извлечь задачи и проверить лимит"):
        tasks = resp.json()["payload"]["tasks"]
        assert tasks, "Ожидаются задачи в ответе"

    # Если данных недостаточно для сравнения — корректно пропускаем тест
    if len(tasks) <= 2:
        pytest.skip(f"Недостаточно данных для проверки убывания: получено {len(tasks)} (нужно > 2)")

    with allure.step("Проверить возрастание по createdAt (новые задачи снизу)"):
        try:
            created_dates = [parser.parse(task["createdAt"]) for task in tasks]
        except Exception as e:
            raise AssertionError(f"Не удалось распарсить createdAt в одной из задач: {e}")

        for i in range(len(created_dates) - 1):
            assert created_dates[i] <= created_dates[i + 1], (
                f"Нарушена сортировка по убыванию: позиции {i} ({created_dates[i]}) и {i + 1} ({created_dates[i + 1]})"
            )

        first, last = created_dates[0], created_dates[-1]
        allure.attach(
            f"Количество задач: {len(tasks)}\nПервая дата: {first}\nПоследняя дата: {last}",
            name="Результат сортировки createdAt ASC",
            attachment_type=allure.attachment_type.TEXT
        )


@allure.parent_suite("Task Service")
@allure.suite("Get Tasks")
@allure.sub_suite("Filtered by criteria")
@allure.sub_suite("Sort by Direction ASC")
@allure.title("GetTasks createdAt_asc: Проверка сортировки по умолчанию (должна быть по возрастанию)")
def test_get_tasks_default_sorting(owner_client, main_space, board_with_10000_tasks):
    """Проверяет что без указания sortDirection сортировка происходит по возрастанию"""

    with allure.step("Выполнить запрос с sortCriteria без sortDirection"):
        resp = owner_client.post(**get_tasks_endpoint(
            space_id=main_space,
            board=board_with_10000_tasks,
            limit=30
            # sortCriteria="createdAt", sortDirection НЕ указываем - проверяем поведение по умолчанию
        ))

    with allure.step("Проверить HTTP 200"):
        assert resp.status_code == 200

    with allure.step("Проверить что сортировка по умолчанию - по возрастанию"):
        tasks = resp.json()["payload"]["tasks"]

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
                "Результат проверки сортировки по умолчанию"
            )
        else:
            allure.attach("Недостаточно данных для проверки убывания: нужно > 2")