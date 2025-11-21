import random
import allure
import pytest

from tests.test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.task_service.utils import delete_task_with_retry

pytestmark = [pytest.mark.backend]

def get_parent_task_subtask_count(client, space_id, task_id) -> int:
    resp = client.post(**get_task_endpoint(slug_id=task_id, space_id=space_id))
    resp.raise_for_status()
    task = resp.json()["payload"]["task"]
    # В ответе список подзадач в ключе 'subtasks'
    assert "subtasks" in task, "'subtasks' отсутствует в родительской задаче"
    return len(task["subtasks"])


@allure.parent_suite("create_task")
@allure.title("Проверка счетчика сабтасок в taskTable в родительской задаче")
def test_parent_task_total_subtask_count_increases_after_subtask_creation(owner_client, main_space,create_task_in_main):
    """
    Тест проверяет увеличение счетчика total сабтасок у родительской задачи после добавления сабтасок.
    """
    client = owner_client
    # Создадим родительскую задачу без сабтасок
    parent_task = create_task_in_main("owner_client", name="Parent task for total subtask count test")
    parent_task_id = parent_task["_id"]
    created_subtask_ids = []

    try:
        with allure.step("Получаем начальное значение total у родительской задачи"):
            initial_total = get_parent_task_subtask_count(client, main_space, parent_task_id)
            assert initial_total == 0

        with allure.step("Создаем первую сабтаску с указанием родительской задачи"):
            subtask1 = create_task_in_main(
                "owner_client",
                parent_task=parent_task_id,
                name="Subtask 1 for parent task total count test",
            )
            created_subtask_ids.append(subtask1["_id"])

        with allure.step("Проверяем, что total увеличился на 1"):
            total_after_first = get_parent_task_subtask_count(client, main_space, parent_task_id)
            assert total_after_first == initial_total + 1, f"Ожидался total={initial_total + 1}, получили {total_after_first}"

        with allure.step("Создаем последовательно рандомное количество сабтасок (от 1 до 10) и проверяем total"):
            random_count = random.randint(1, 10)
            for i in range(1, random_count + 1):
                subtask = create_task_in_main(
                    "owner_client",
                    parent_task=parent_task_id,
                    name=f"Random subtask #{i} for parent task total count test",
                )
                created_subtask_ids.append(subtask["_id"])

                expected_total = initial_total + 1 + i
                actual_total = get_parent_task_subtask_count(client, main_space, parent_task_id)
                assert actual_total == expected_total, f"После добавления {i} сабтасок ожидали total={expected_total}, получили {actual_total}"

        with allure.step("Проверяем итоговое значение total после добавления всех сабтасок"):
            final_total = get_parent_task_subtask_count(client, main_space, parent_task_id)
            expected_final = initial_total + 1 + random_count
            assert final_total == expected_final, f"Ожидался total={expected_final}, получили {final_total}"

    finally:
        with allure.step("Удаляем все созданные сабтаски и родительскую задачу"):
            for subtask_id in created_subtask_ids:
                delete_task_with_retry(client, subtask_id, main_space)
            delete_task_with_retry(client, parent_task_id, main_space)


@allure.parent_suite("create_task")
@allure.title("Проверка уменьшения счетчика сабтасок после удаления сабтасок в родительской задаче")
def test_parent_task_total_subtask_count_decrease_after_subtask_deletion(owner_client, main_space, create_task_in_main):
    """
    Тест проверяет корректное уменьшение счетчика total сабтасок после удаления подзадач.
    """
    client = owner_client
    # Создаем родительскую задачу
    parent_task = create_task_in_main("owner_client", name="Parent task for decrease subtask total test")
    parent_task_id = parent_task["_id"]
    created_subtask_ids = []

    try:
        with allure.step("Создаем рандомное количество сабтасок (от 1 до 10) для родительской задачи"):
            random_count = random.randint(1, 10)
            for i in range(1, random_count + 1):
                subtask = create_task_in_main(
                    "owner_client",
                    parent_task=parent_task_id,
                    name=f"Subtask #{i} for decrease subtask total test",
                )
                created_subtask_ids.append(subtask["_id"])

        with allure.step("Проверяем, что total соответствует количеству созданных сабтасок"):
            total_after_creation = get_parent_task_subtask_count(client, main_space, parent_task_id)
            assert total_after_creation == random_count, f"Ожидалось total={random_count}, получили {total_after_creation}"

        with allure.step("Удаляем сабтаски по одной и проверяем decrement total пока их кол-во не станет равным 0"):
            for index, subtask_id in enumerate(created_subtask_ids, 1):
                delete_task_with_retry(client, subtask_id, main_space)
                expected_total = random_count - index
                actual_total = get_parent_task_subtask_count(client, main_space, parent_task_id)
                assert actual_total == expected_total, f"После удаления {index} сабтасок ожидали total={expected_total}, получили {actual_total}"

    finally:
        with allure.step("Удаляем сабтаски и родительскую задачу принудительно (на случай если тесты упадут)"):
            for subtask_id in created_subtask_ids:
                try:
                    delete_task_with_retry(client, subtask_id, main_space)
                except Exception:
                    pass
            delete_task_with_retry(client, parent_task_id, main_space)