import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Multiaction")
@allure.suite("Completed")
@allure.sub_suite("Positive")
@allure.title("completed=True для нескольких задач")
def test_mark_completed(owner_client, main_space, make_task_in_main):
    """
    Выбираем несколько незавершённых задач, применяем completed=True.
    Все задачи должны попасть в success и стать completed.
    """
    with allure.step("Создаём 3 незавершённые задачи"):
        tasks = [make_task_in_main({"name": f"complete-test-{i}", "completed": False}) for i in range(3)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Применяем MultipleEditTasks completed=True"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            completed=True,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали все задачи в success: {task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что задачи стали completed"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["completed"] is True, f"Задача {tid} не стала completed: {task.get('completed')}"


@allure.parent_suite("Multiaction")
@allure.suite("Completed")
@allure.sub_suite("Positive")
@allure.title("completed=False — снятие completed")
def test_mark_not_completed(owner_client, main_space, make_task_in_main):
    """
    Выбираем несколько завершённых задач, применяем completed=False.
    Все задачи должны попасть в success и стать not completed.
    """
    with allure.step("Создаём 3 завершённые задачи"):
        tasks = [make_task_in_main({"name": f"uncomplete-test-{i}", "completed": True}) for i in range(3)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Применяем MultipleEditTasks completed=False"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            completed=False,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали все задачи в success: {task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что задачи стали not completed"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["completed"] is False, f"Задача {tid} не стала not completed: {task.get('completed')}"


@allure.parent_suite("Multiaction")
@allure.suite("Completed")
@allure.sub_suite("Positive")
@allure.title("Mixed state: completed=True при смешанном состоянии задач")
def test_mark_completed_mixed_state(owner_client, main_space, make_task_in_main):
    """
    Часть задач уже completed, часть нет. Применяем completed=True.
    Реально изменённые — в success, уже completed — в skipped.
    """
    with allure.step("Создаём 2 незавершённые и 1 завершённую задачу"):
        not_completed = [make_task_in_main({"name": f"mixed-nc-{i}", "completed": False}) for i in range(2)]
        completed = [make_task_in_main({"name": "mixed-c-0", "completed": True})]
        nc_ids = [t["_id"] for t in not_completed]
        c_ids = [t["_id"] for t in completed]
        all_ids = nc_ids + c_ids

    with allure.step("Применяем MultipleEditTasks completed=True"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=all_ids,
            completed=True,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что реально изменённые задачи попали в success"):
        assert sorted(payload["success"]) == sorted(nc_ids), (
            f"Ожидали success={nc_ids}, получили: {payload['success']}"
        )

    with allure.step("Проверяем, что уже completed задачи попали в skipped"):
        assert sorted(payload["skipped"]) == sorted(c_ids), (
            f"Ожидали skipped={c_ids}, получили: {payload['skipped']}"
        )

    with allure.step("Проверяем, что failed пуст"):
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что все задачи completed"):
        for tid in all_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["completed"] is True, f"Задача {tid} не completed: {task.get('completed')}"


@allure.parent_suite("Multiaction")
@allure.suite("Completed")
@allure.sub_suite("Positive")
@allure.title("Mixed state: completed=False при смешанном состоянии задач")
def test_mark_not_completed_mixed_state(owner_client, main_space, make_task_in_main):
    """
    Часть задач completed, часть нет. Применяем completed=False.
    Реально изменённые — в success, уже незавершённые — в skipped.
    """
    with allure.step("Создаём 2 завершённые и 1 незавершённую задачу"):
        completed = [make_task_in_main({"name": f"mixed-c-{i}", "completed": True}) for i in range(2)]
        not_completed = [make_task_in_main({"name": "mixed-nc-0", "completed": False})]
        c_ids = [t["_id"] for t in completed]
        nc_ids = [t["_id"] for t in not_completed]
        all_ids = c_ids + nc_ids

    with allure.step("Применяем MultipleEditTasks completed=False"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=all_ids,
            completed=False,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что реально изменённые задачи попали в success"):
        assert sorted(payload["success"]) == sorted(c_ids), (
            f"Ожидали success={c_ids}, получили: {payload['success']}"
        )

    with allure.step("Проверяем, что уже незавершённые задачи попали в skipped"):
        assert sorted(payload["skipped"]) == sorted(nc_ids), (
            f"Ожидали skipped={nc_ids}, получили: {payload['skipped']}"
        )

    with allure.step("Проверяем, что failed пуст"):
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что все задачи not completed"):
        for tid in all_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["completed"] is False, f"Задача {tid} не стала not completed: {task.get('completed')}"
