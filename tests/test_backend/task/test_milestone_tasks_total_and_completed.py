import random
import allure
import pytest

from test_backend.data.endpoints.milestone.milestones_endpoints import get_milestone_endpoint
from test_backend.task.utils import delete_task_with_retry, get_named_milestone_id

pytestmark = [pytest.mark.backend]

def get_milestone_total(client, space_id, milestone_id):
    resp = client.post(**get_milestone_endpoint(space_id=space_id, ms_id=milestone_id))
    resp.raise_for_status()
    milestone = resp.json()["payload"]["milestone"]
    assert "total" in milestone, "'total' отсутствует в milestone"
    return milestone["total"]

def get_milestone_completed(client, space_id, milestone_id):
    """
    Получает количество завершённых задач (completed=True) для milestone.
    """
    resp = client.post(**get_milestone_endpoint(space_id=space_id, ms_id=milestone_id))
    resp.raise_for_status()
    milestone = resp.json()["payload"]["milestone"]
    assert "completed" in milestone, "'completed' отсутствует в milestone"
    return milestone["completed"]


def clear_milestone_tasks(client, space_id, milestone_id):
    resp = client.post(**get_milestone_endpoint(space_id=space_id, ms_id=milestone_id))
    resp.raise_for_status()
    tasks = resp.json()["payload"]["milestone"].get("tasks", [])
    for task_id in tasks:
        delete_task_with_retry(client, task_id, space_id)
    total_after_cleanup = get_milestone_total(client, space_id, milestone_id)
    assert total_after_cleanup == 0, f"После удаления всех задач total должен быть 0, а получил {total_after_cleanup}"


@allure.title("Проверка увеличения счетчика задач у milestone после создания задач и соответствия completed")
def test_milestone_total_and_completed_after_task_creation(owner_client, main_space, create_task_in_main, main_board):
    """
    Тест проверяет:
    - увеличение счетчика total задач у milestone после создания задач,
    - и что completed-задачи учитываются корректно (через get_milestone_completed).
    """
    milestone_name = "Milestone total task count"
    client = owner_client
    milestone_id = get_named_milestone_id(client, main_space, main_board, milestone_name)
    created_task_ids = []
    completed_task_ids = []

    try:
        with allure.step("Получаем начальное значение total у milestone"):
            initial_total = get_milestone_total(client, main_space, milestone_id)

        if initial_total != 0:
            with allure.step("Очищаем milestone от задач, проверяем что total стал 0"):
                clear_milestone_tasks(client, main_space, milestone_id)
                initial_total = get_milestone_total(client, main_space, milestone_id)
                assert initial_total == 0
                initial_completed = get_milestone_completed(client, main_space, milestone_id)
                assert initial_completed == 0


        with allure.step("Создаём первую задачу с этим milestone"):
            task1 = create_task_in_main(
                "owner_client",
                milestones=[milestone_id],
                name="Task 1 for milestone total count test",
            )
            created_task_ids.append(task1["_id"])
            if task1.get("completed"):  # Только если True!
                completed_task_ids.append(task1["_id"])

        with allure.step("Проверяем, что total и complited корректны после создания первой задачи"):
            total_after_first = get_milestone_total(client, main_space, milestone_id)
            completed_after_first = get_milestone_completed(client, main_space, milestone_id)
            assert total_after_first == initial_total + 1, f"Ожидался total={initial_total + 1}, получили {total_after_first}"
            assert completed_after_first == len(completed_task_ids), f"Ожидалось completed={len(completed_task_ids)}, получили {completed_after_first}"

        with allure.step("Создаём последовательно рандомное количество задач (от 1 до 10) с этим milestone, completed=random и каждый раз проверяем  total и completed"):
            random_count = random.randint(1, 10)
            for i in range(1, random_count + 1):
                task = create_task_in_main(
                    "owner_client",
                    milestones=[milestone_id],
                    name=f"Random task #{i} for milestone total count test",
                )
                created_task_ids.append(task["_id"])
                if task.get("completed"):  # добавляем только если completed = true
                    completed_task_ids.append(task["_id"])

                expected_total = initial_total + 1 + i
                actual_total = get_milestone_total(client, main_space, milestone_id)
                assert actual_total == expected_total, f"После добавления {i} задач ожидали total={expected_total}, получили {actual_total}"

                expected_completed = len(completed_task_ids)
                actual_completed = get_milestone_completed(client, main_space, milestone_id)
                assert expected_completed == actual_completed, f"Ожидалось completed={expected_completed}, получили {actual_completed}"

        with allure.step("Проверяем итоговое значение total и complited после добавления всех задач"):
            final_total = get_milestone_total(client, main_space, milestone_id)
            expected_final = initial_total + 1 + random_count
            assert final_total == expected_final, f"Ожидался total={expected_final}, получили {final_total}"

            expected_completed = len(completed_task_ids)
            actual_completed = get_milestone_completed(client, main_space, milestone_id)
            assert expected_completed == actual_completed, f"Ожидалось completed={expected_completed}, получили {actual_completed}"


    finally:
        with allure.step("Удаляем все созданные задачи"):
            for task_id in created_task_ids:
                delete_task_with_retry(client, task_id, main_space)


@allure.title("Проверка уменьшения счетчика задач milestone после удаления задач")
def test_milestone_total_task_count_decrease_after_task_deletion(owner_client, main_space, create_task_in_main, main_board):
    """
    Тест проверяет корректное уменьшение счетчика total после удаления задач и ожидает total=0 в конце.
    """
    milestone_name = "Milestone total task count"
    client = owner_client
    milestone_id = get_named_milestone_id(client, main_space, main_board, milestone_name)
    created_task_ids = []

    try:
        with allure.step("Получаем начальное значение total у milestone"):
            initial_total = get_milestone_total(client, main_space, milestone_id)

        if initial_total != 0:
            with allure.step("Очищаем milestone от задач, проверяем что total = 0"):
                clear_milestone_tasks(client, main_space, milestone_id)
            assert initial_total == 0

        with allure.step("Создаём рандомное кол-во задач  (от 1 до 10) с этим milestone"):
            random_count = random.randint(1, 10)
            for i in range(1, random_count + 1):
                task = create_task_in_main(
                    "owner_client",
                    milestones=[milestone_id],
                    name=f"Task #{i} for milestone decrease test",
                )
                created_task_ids.append(task["_id"])

        with allure.step("Проверяем, что total соответствует количеству созданных задач"):
            total_after_creation = get_milestone_total(client, main_space, milestone_id)
            assert total_after_creation == random_count, f"Ожидалось total={random_count}, получили {total_after_creation}"

        with allure.step("Удаляем задачи по одной и проверяем decrement total"):
            for index, task_id in enumerate(created_task_ids, 1): # 1 задаёт начальное значение счётчика индекса(по умолчанию=0).
                delete_task_with_retry(client, task_id, main_space)
                expected_total = random_count - index
                actual_total = get_milestone_total(client, main_space, milestone_id)
                assert actual_total == expected_total, f"После удаления {index} задач ожидали total={expected_total}, получили {actual_total}"

    finally:
        with allure.step("Финальная очистка созданных задач"):
            for task_id in created_task_ids:
                try:
                    delete_task_with_retry(client, task_id, main_space)
                except Exception:
                    pass

# TODO: Добавить тесты для проверки корректности обновления счетчика total при архивировании задач в milestone.
# Сейчас проверяем только добавление и удаление задач. Архивация пока не покрыта.
with allure.step("TODO: В будущем - проверить изменение total при архивировании задач"):
    pass