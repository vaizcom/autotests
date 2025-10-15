import random

import allure
import pytest

from test_backend.data.endpoints.milestone.milestones_endpoints import get_milestone_endpoint
from test_backend.task.utils import delete_task_with_retry, get_named_milestone_id

pytestmark = [pytest.mark.backend]

@allure.story("Проверка счетчика задач у существующего milestone 'Milestone total task count'")
def test_milestone_total_task_count_increases_after_task_creation(
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

        with allure.step("Создаём рандомное количество задач с этим milestone (от 1 до 10) Проверяем, что при добавлении"
                         " задач, счетчик total увеличивается корректно "):
            random_count = random.randint(1, 10)
            for i in range(random_count):
                task = create_task_in_main(
                    "owner_client",
                    milestones=[milestone_id],
                    name=f"Random task #{i + 1} for milestone total count test"
                )
                created_task_ids.append(task["_id"])

                expected_total = initial_total + 1 + (i + 1)
                total_after_create = get_total()
                assert total_after_create == expected_total, \
                    f"После добавления {i + 1} задач ожидали total={expected_total}, получили {total_after_create}"

        with allure.step(f"Проверяем, что total увеличился на рандомное количество = {random_count}"):
            total_after = get_total()
            assert total_after == initial_total + 1 + random_count, \
                f"Ожидалось total={initial_total + random_count}, получили {total_after}"


    finally:
        with allure.step("Удаляем созданные задачи после теста"):
            for task_id in created_task_ids:
                delete_task_with_retry(client, task_id, main_space)


@allure.story("Проверка уменьшения счетчика задач milestone после удаления задач")
def test_milestone_total_task_count_decrease_after_task_deletion(
    owner_client, main_space, create_task_in_main, main_board
):
    """
    Проверяем, что при удалении задач с milestone счетчик total уменьшается корректно,
    и в итоге становится 0 после удаления всех задач.
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
        with allure.step("Очищаем milestone от задач перед тестом"):
            resp = client.post(**get_milestone_endpoint(space_id=main_space, ms_id=milestone_id))
            resp.raise_for_status()
            tasks = resp.json()["payload"]["milestone"].get("tasks", [])
            for task in tasks:
                delete_task_with_retry(client, task, main_space)
            assert get_total() == 0, "Ожидалось, что total будет 0 после очистки"

        with allure.step("Создаём несколько задач с этим milestone"):
            count = 5
            for i in range(count):
                task = create_task_in_main(
                    "owner_client",
                    milestones=[milestone_id],
                    name=f"Task #{i + 1} for milestone decrease test"
                )
                created_task_ids.append(task["_id"])

        with allure.step("Проверяем, что total соответствует количеству созданных задач"):
            total_after_creation = get_total()
            assert total_after_creation == count, f"Ожидали total={count}, получили {total_after_creation}"

        with allure.step("Удаляем задачи по одной и проверяем decrement total"):
            for index, task_id in enumerate(created_task_ids):
                delete_task_with_retry(client, task_id, main_space)
                expected_total = count - (index + 1)
                total_after_delete = get_total()
                assert total_after_delete == expected_total, \
                    f"После удаления {index + 1} задач ожидали total={expected_total}, получили {total_after_delete}"

    finally:
        # На всякий случай удаляем оставшиеся задачи
        with allure.step("Финальная очистка created задач"):
            for task_id in created_task_ids:
                # Проверяем, что задача еще не удалена (возможно, уже удалена выше)
                try:
                    delete_task_with_retry(client, task_id, main_space)
                except Exception:
                    pass


# TODO: Добавить тесты для проверки корректности обновления счетчика total
# при архивировании задач в milestone.
# Сейчас проверяем только добавление и удаление задач. Архивация пока не покрыта.
with allure.step("TODO: В будущем - проверить изменение total при архивировании задач"):
    pass