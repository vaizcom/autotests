import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.data.endpoints.Task.constants import PRIORITY_LOW, PRIORITY_GENERAL, PRIORITY_MEDIUM, PRIORITY_HIGH

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Multiaction")
@allure.suite("Priority")
@allure.sub_suite("Positive")
@allure.title("Установить priority на нескольких задачах")
def test_set_priority(owner_client, main_space, make_task_in_main):
    """
    Задачи с Default приоритетом (без приоритета GENERAL), применяем MEDIUM.
    Все задачи в success, GetTask подтверждает.
    """
    with allure.step("Создаём 2 задачи с Default приоритетом (без приоритета)"):
        tasks = [make_task_in_main({"name": f"priority-set-{i}", "priority": PRIORITY_GENERAL}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Применяем MultipleEditTasks priority=MEDIUM"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            priority=PRIORITY_MEDIUM,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали все задачи в success: {task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что priority=MEDIUM"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["priority"] == PRIORITY_MEDIUM, f"Задача {tid}: ожидали priority={PRIORITY_MEDIUM}, получили {task.get('priority')}"


@allure.parent_suite("Multiaction")
@allure.suite("Priority")
@allure.sub_suite("Positive")
@allure.title("Сменить priority на другой")
def test_change_priority(owner_client, main_space, make_task_in_main):
    """
    Задачи с MEDIUM, повышаем до HIGH.
    Все в success.
    """
    with allure.step("Создаём 2 задачи с priority=MEDIUM"):
        tasks = [make_task_in_main({"name": f"priority-change-{i}", "priority": PRIORITY_MEDIUM}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Применяем MultipleEditTasks priority=HIGH"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            priority=PRIORITY_HIGH,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали все задачи в success: {task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что priority=HIGH"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["priority"] == PRIORITY_HIGH, f"Задача {tid}: ожидали priority={PRIORITY_HIGH}, получили {task.get('priority')}"


@allure.parent_suite("Multiaction")
@allure.suite("Priority")
@allure.sub_suite("Positive")
@allure.title("Сбросить priority (GENERAL)")
def test_reset_priority(owner_client, main_space, make_task_in_main):
    """
    Задачи с MEDIUM, сбрасываем в GENERAL (дефолт).
    Все в success.
    """
    with allure.step("Создаём 2 задачи с priority=MEDIUM"):
        tasks = [make_task_in_main({"name": f"priority-reset-{i}", "priority": PRIORITY_MEDIUM}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Применяем MultipleEditTasks priority=GENERAL"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            priority=PRIORITY_GENERAL,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали все задачи в success: {task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что priority=GENERAL"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["priority"] == PRIORITY_GENERAL, f"Задача {tid}: ожидали priority={PRIORITY_GENERAL}, получили {task.get('priority')}"


@allure.parent_suite("Multiaction")
@allure.suite("Priority")
@allure.sub_suite("Positive")
@allure.title("Понизить priority (LOW)")
def test_downgrade_priority(owner_client, main_space, make_task_in_main):
    """
    Задачи с HIGH, понижаем до LOW.
    Все в success.
    """
    with allure.step("Создаём 2 задачи с priority=HIGH"):
        tasks = [make_task_in_main({"name": f"priority-downgrade-{i}", "priority": PRIORITY_HIGH}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Применяем MultipleEditTasks priority=LOW"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            priority=PRIORITY_LOW,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали все задачи в success: {task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что priority=LOW"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["priority"] == PRIORITY_LOW, f"Задача {tid}: ожидали priority={PRIORITY_LOW}, получили {task.get('priority')}"


@allure.parent_suite("Multiaction")
@allure.suite("Priority")
@allure.sub_suite("Positive")
@allure.title("Mixed state: часть задач уже с нужным приоритетом")
def test_set_priority_mixed_state(owner_client, main_space, make_task_in_main):
    """
    Часть задач уже с MEDIUM, часть с GENERAL.
    Применяем MEDIUM: изменённые в success, совпадающие в skipped.
    """
    with allure.step("Создаём 2 задачи с priority=GENERAL и 1 задачу с priority=MEDIUM"):
        different = [make_task_in_main({"name": f"mixed-p1-{i}", "priority": PRIORITY_GENERAL}) for i in range(2)]
        same = [make_task_in_main({"name": "mixed-p2-0", "priority": PRIORITY_MEDIUM})]
        diff_ids = [t["_id"] for t in different]
        same_ids = [t["_id"] for t in same]
        all_ids = diff_ids + same_ids

    with allure.step("Применяем MultipleEditTasks priority=MEDIUM"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=all_ids,
            priority=PRIORITY_MEDIUM,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что изменённые задачи в success"):
        assert sorted(payload["success"]) == sorted(diff_ids), (
            f"Ожидали success={diff_ids}, получили: {payload['success']}"
        )

    with allure.step("Проверяем, что задачи с тем же приоритетом в skipped"):
        assert sorted(payload["skipped"]) == sorted(same_ids), (
            f"Ожидали skipped={same_ids}, получили: {payload['skipped']}"
        )

    with allure.step("Проверяем, что failed пуст"):
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что все задачи priority=MEDIUM"):
        for tid in all_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["priority"] == PRIORITY_MEDIUM, f"Задача {tid}: ожидали priority={PRIORITY_MEDIUM}, получили {task.get('priority')}"
