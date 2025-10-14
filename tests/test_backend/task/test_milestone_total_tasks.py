import random

import allure
import pytest

from test_backend.data.endpoints.milestone.milestones_endpoints import get_milestone_endpoint
from test_backend.task.utils import delete_task_with_retry, get_named_milestone_id

pytestmark = [pytest.mark.backend]

@allure.story("Проверка счетчика задач у существующего milestone 'Milestone total task count'")
def test_milestone_total_task_count(
    owner_client, main_space, create_task_in_main
, main_board):
    """
    Используем существующий milestone с именем "Milestone total task count".
    Проверяем initial total,
    создаём задачу и проверяем total == initial + 1,
    создаём рандомное кол-во и проверяем total == initial + 1 + random_count.
    В конце удаляем созданные задачи.
    """

    client = owner_client
    milestone_name = "Milestone total task count"
    milestone_id = get_named_milestone_id(client, main_space, main_board, milestone_name)

    created_task_ids = []

    def get_total():
        resp = client.post(**get_milestone_endpoint(space_id=main_space, ms_id=milestone_id))
        resp.raise_for_status()
        ms = resp.json()["payload"]["milestone"]
        assert "total" in ms, "'total' отсутствует в milestone"
        return ms["total"]

    try:
        with allure.step("Получаем начальное значение total у milestone"):
            initial_total = get_total()

        # Проверка total и при необходимости удаление всех задач, чтобы total стал 0
        if initial_total != 0:
            # Получаем список всех задач с этим milestone
            resp = client.post(**get_milestone_endpoint(space_id=main_space, ms_id=milestone_id))
            resp.raise_for_status()
            tasks = resp.json()["payload"]["milestone"].get("tasks", [])
            for task in tasks:
                delete_task_with_retry(client, task, main_space)
            # Проверяем, что total теперь 0
            total_after_cleanup = get_total()
            assert total_after_cleanup == 0, f"После удаления всех задач total ожидается 0, получил {total_after_cleanup}"
            initial_total = 0  # Обновляем initial_total для дальнейших проверок

        with allure.step("Создаём первую задачу с этим milestone"):
                task1 = create_task_in_main(
                    "owner_client",
                    milestones=[milestone_id],
                    name="Task 1 for milestone total count test",
                )
                created_task_ids.append(task1["_id"])

        with allure.step("Проверяем, что total увеличился на 1"):
            total_after_first = get_total()
            assert total_after_first == initial_total + 1, \
                f"Ожидалось total={initial_total + 1}, получили {total_after_first}"

        with allure.step("Создаём рандомное количество задач с этим milestone (от 1 до 10)"):
            random_count = random.randint(1, 10)
            for i in range(random_count):
                task = create_task_in_main(
                    "owner_client",
                    milestones=[milestone_id],
                    name=f"Random task #{i + 1} for milestone total count test"
                )
                created_task_ids.append(task["_id"])

        with allure.step(f"Проверяем, что total увеличился на {random_count}"):
            total_after = get_total()
            assert total_after == initial_total + 1 + random_count, \
                f"Ожидалось total={initial_total + random_count}, получили {total_after}"


    finally:
        with allure.step("Удаляем созданные задачи после теста"):
            for task_id in created_task_ids:
                delete_task_with_retry(client, task_id, main_space)