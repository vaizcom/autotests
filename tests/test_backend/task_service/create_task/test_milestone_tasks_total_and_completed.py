import random
import time
import allure
import pytest

from config.generators import generate_date
from test_backend.data.endpoints.milestone.milestones_endpoints import (
    create_milestone_endpoint, get_milestone_endpoint, archive_milestone_endpoint,
    get_milestones_endpoint,
)
from test_backend.task_service.utils import delete_task_with_retry

pytestmark = [pytest.mark.backend]


def get_milestone_counters(client, space_id, milestone_id):
    """Возвращает (total, completed) для milestone."""
    resp = client.post(**get_milestone_endpoint(space_id=space_id, ms_id=milestone_id))
    resp.raise_for_status()
    ms = resp.json()["payload"]["milestone"]
    return ms["total"], ms["completed"]


def wait_milestone_total(client, space_id, milestone_id, expected_total, timeout=10, poll=0.5):
    """Поллит счётчик total milestone до совпадения с ожидаемым значением или таймаута."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        actual, _ = get_milestone_counters(client, space_id, milestone_id)
        if actual == expected_total:
            return actual
        time.sleep(poll)
    return actual


def cleanup_autotest_milestones(client, space_id, board_id):
    """Архивирует все незаархивированные майлстоуны с префиксом _autotest_, оставшиеся от предыдущих прогонов."""
    resp = client.post(**get_milestones_endpoint(space_id=space_id, board_id=board_id))
    if resp.status_code != 200:
        return
    milestones = resp.json().get("payload", {}).get("milestones", [])
    for ms in milestones:
        if ms.get("name", "").startswith("_autotest_"):
            client.post(**archive_milestone_endpoint(space_id=space_id, milestone_id=ms["_id"]))



@allure.parent_suite("Task Service")
@allure.suite("Create Task")
@allure.title("Проверка увеличения счетчика задач в milestone после создания задач и соответствия completed")
def test_milestone_total_and_completed_after_task_creation(
        owner_client, main_space, main_board, main_project, create_task_in_main,
):
    """
    Создаём чистый milestone, добавляем в него задачи (1-10, completed=random),
    после каждой проверяем что total и completed увеличиваются корректно.
    """
    client = owner_client
    milestone_id = None
    created_task_ids = []

    try:
        with allure.step("Pre-condition: Архивируем _autotest_ майлстоуны от предыдущих прогонов"):
            cleanup_autotest_milestones(client, main_space, main_board)

        with allure.step("Создаём чистый milestone"):
            resp = client.post(**create_milestone_endpoint(
                space_id=main_space, board=main_board, project=main_project,
                name=f"_autotest_total_{generate_date()}",
            ))
            assert resp.status_code == 200, f"Не удалось создать milestone: {resp.text}"
            milestone_id = resp.json()["payload"]["milestone"]["_id"]

        with allure.step("Проверяем что milestone пустой: total=0, completed=0"):
            total, completed = get_milestone_counters(client, main_space, milestone_id)
            assert total == 0 and completed == 0, f"Новый milestone не пустой: total={total}, completed={completed}"

        random_count = random.randint(1, 10)
        expected_completed = 0

        with allure.step(f"Создаём {random_count} задач с milestone, каждый раз проверяем счётчики"):
            for i in range(1, random_count + 1):
                task = create_task_in_main(
                    "owner_client",
                    milestones=[milestone_id],
                    name=f"Task #{i} for milestone total test",
                )
                created_task_ids.append(task["_id"])
                if task.get("completed"):
                    expected_completed += 1

                actual_total, actual_completed = get_milestone_counters(client, main_space, milestone_id)
                assert actual_total == i, \
                    f"После добавления {i} задач: ожидали total={i}, получили {actual_total}"
                assert actual_completed == expected_completed, \
                    f"После добавления {i} задач: ожидали completed={expected_completed}, получили {actual_completed}"

    finally:
        for task_id in created_task_ids:
            delete_task_with_retry(client, task_id, main_space)
        if milestone_id:
            client.post(**archive_milestone_endpoint(space_id=main_space, milestone_id=milestone_id))


@allure.parent_suite("Task Service")
@allure.suite("Create Task")
@allure.title("Проверка уменьшения счетчика задач в milestone после удаления задач")
def test_milestone_total_decrease_after_task_deletion(
        owner_client, main_space, main_board, main_project, create_task_in_main,
):
    """
    Создаём чистый milestone, добавляем задачи (1-10),
    затем удаляем по одной и проверяем что total уменьшается до 0.
    """
    client = owner_client
    milestone_id = None
    created_task_ids = []

    try:
        with allure.step("Pre-condition: Архивируем _autotest_ майлстоуны от предыдущих прогонов"):
            cleanup_autotest_milestones(client, main_space, main_board)

        with allure.step("Создаём чистый milestone"):
            resp = client.post(**create_milestone_endpoint(
                space_id=main_space, board=main_board, project=main_project,
                name=f"_autotest_decrease_{generate_date()}",
            ))
            assert resp.status_code == 200, f"Не удалось создать milestone: {resp.text}"
            milestone_id = resp.json()["payload"]["milestone"]["_id"]

        random_count = random.randint(1, 10)

        with allure.step(f"Создаём {random_count} задач с milestone"):
            for i in range(1, random_count + 1):
                task = create_task_in_main(
                    "owner_client",
                    milestones=[milestone_id],
                    name=f"Task #{i} for milestone decrease test",
                )
                created_task_ids.append(task["_id"])

        with allure.step(f"Проверяем total={random_count} после создания"):
            total, _ = get_milestone_counters(client, main_space, milestone_id)
            assert total == random_count, f"Ожидалось total={random_count}, получили {total}"

        with allure.step("Удаляем задачи по одной и проверяем decrement total"):
            for index, task_id in enumerate(created_task_ids, 1):
                delete_task_with_retry(client, task_id, main_space, retries=3, delay=1)
                expected_total = random_count - index
                actual_total = wait_milestone_total(client, main_space, milestone_id, expected_total)
                assert actual_total == expected_total, \
                    f"После удаления {index} задач: ожидали total={expected_total}, получили {actual_total}"
            # Задачи уже удалены в цикле, очищаем список чтобы finally не удалял повторно
            created_task_ids.clear()

        with allure.step("Финальная проверка: total=0"):
            total, completed = get_milestone_counters(client, main_space, milestone_id)
            assert total == 0, f"После удаления всех задач ожидали total=0, получили {total}"
            assert completed == 0, f"После удаления всех задач ожидали completed=0, получили {completed}"

    finally:
        for task_id in created_task_ids:
            delete_task_with_retry(client, task_id, main_space)
        if milestone_id:
            client.post(**archive_milestone_endpoint(space_id=main_space, milestone_id=milestone_id))
