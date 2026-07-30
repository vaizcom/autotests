import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint

pytestmark = [pytest.mark.backend]


def _get_task_assignees(client, space_id, task_id):
    """Получает список assignees задачи через GetTask."""
    r = client.post(**get_task_endpoint(space_id=space_id, slug_id=task_id))
    assert r.status_code == 200, r.text
    return r.json()["payload"]["task"].get("assignees", [])


@allure.parent_suite("Multiaction")
@allure.suite("Assignees")
@allure.sub_suite("Positive")
@allure.title("Add assignee на задачи без assignees")
def test_add_assignee(owner_client, main_space, make_task_in_main, main_personal):
    """
    Задачи без assignees, добавляем одного.
    Все задачи в success, GetTask подтверждает.
    """
    assignee_id = main_personal["owner"][0]

    with allure.step("Создаём 2 задачи без assignees"):
        tasks = [make_task_in_main({"name": f"assignee-add-{i}"}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step(f"Применяем MultipleEditTasks assignees=[id, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            assignees=[assignee_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали success={task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что assignee назначен"):
        for tid in task_ids:
            assignees = _get_task_assignees(owner_client, main_space, tid)
            assert assignee_id in assignees, (
                f"Задача {tid}: ожидали {assignee_id} в assignees, получили: {assignees}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Assignees")
@allure.sub_suite("Positive")
@allure.title("Add assignee не заменяет существующего")
def test_add_assignee_keeps_existing(owner_client, main_space, make_task_in_main, main_personal):
    """
    Задачи уже с assignee (owner), добавляем другого (member).
    Оба assignee на задаче.
    """
    owner_id = main_personal["owner"][0]
    member_id = main_personal["member"][0]

    with allure.step("Создаём 2 задачи с assignee=owner"):
        tasks = [make_task_in_main({"name": f"assignee-keep-{i}", "assignees": [owner_id]}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Добавляем member через MultipleEditTasks"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            assignees=[member_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали success={task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что оба assignee на задаче"):
        for tid in task_ids:
            assignees = _get_task_assignees(owner_client, main_space, tid)
            assert owner_id in assignees, f"Задача {tid}: owner пропал из assignees: {assignees}"
            assert member_id in assignees, f"Задача {tid}: member не добавлен в assignees: {assignees}"


@allure.parent_suite("Multiaction")
@allure.suite("Assignees")
@allure.sub_suite("Positive")
@allure.title("Два последовательных add — оба assignee на задаче")
def test_add_two_assignees_sequentially(owner_client, main_space, make_task_in_main, main_personal):
    """
    Задачи без assignees. Два последовательных вызова add с разными member_id.
    Оба assignee на задаче.
    """
    owner_id = main_personal["owner"][0]
    member_id = main_personal["member"][0]

    with allure.step("Создаём 2 задачи без assignees"):
        tasks = [make_task_in_main({"name": f"assignee-seq-{i}"}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Первый add — owner"):
        resp1 = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            assignees=[owner_id, "add"],
        ))
        payload1 = assert_multiaction_response(resp1)
        assert sorted(payload1["success"]) == sorted(task_ids)
        assert payload1["failed"] == [], f"failed не пуст: {payload1['failed']}"
        assert payload1["skipped"] == [], f"skipped не пуст: {payload1['skipped']}"

    with allure.step("Второй add — member"):
        resp2 = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            assignees=[member_id, "add"],
        ))
        payload2 = assert_multiaction_response(resp2)
        assert sorted(payload2["success"]) == sorted(task_ids)
        assert payload2["failed"] == [], f"failed не пуст: {payload2['failed']}"
        assert payload2["skipped"] == [], f"skipped не пуст: {payload2['skipped']}"

    with allure.step("Проверяем через GetTask, что оба assignee на задаче"):
        for tid in task_ids:
            assignees = _get_task_assignees(owner_client, main_space, tid)
            assert owner_id in assignees, f"Задача {tid}: owner не в assignees: {assignees}"
            assert member_id in assignees, f"Задача {tid}: member не в assignees: {assignees}"


@allure.parent_suite("Multiaction")
@allure.suite("Assignees")
@allure.sub_suite("Positive")
@allure.title("Remove assignee")
def test_remove_assignee(owner_client, main_space, make_task_in_main, main_personal):
    """
    Задачи с одним assignee, убираем его.
    Все в success, assignees пуст.
    """
    assignee_id = main_personal["owner"][0]

    with allure.step("Создаём 2 задачи с assignee"):
        tasks = [make_task_in_main({"name": f"assignee-rm-{i}", "assignees": [assignee_id]}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Убираем assignee через MultipleEditTasks"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            assignees=[assignee_id, "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали success={task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что assignees пуст"):
        for tid in task_ids:
            assignees = _get_task_assignees(owner_client, main_space, tid)
            assert assignee_id not in assignees, (
                f"Задача {tid}: assignee не удалён: {assignees}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Assignees")
@allure.sub_suite("Positive")
@allure.title("Remove одного из нескольких assignees — второй остаётся")
def test_remove_one_of_multiple_assignees(owner_client, main_space, make_task_in_main, main_personal):
    """
    Задачи с двумя assignees, убираем одного.
    Второй остаётся.
    """
    owner_id = main_personal["owner"][0]
    member_id = main_personal["member"][0]

    with allure.step("Создаём 2 задачи с двумя assignees"):
        tasks = [make_task_in_main({"name": f"assignee-partial-rm-{i}", "assignees": [owner_id, member_id]}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Убираем owner через MultipleEditTasks"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            assignees=[owner_id, "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids), (
            f"Ожидали success={task_ids}, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что owner убран, member остался"):
        for tid in task_ids:
            assignees = _get_task_assignees(owner_client, main_space, tid)
            assert owner_id not in assignees, f"Задача {tid}: owner не удалён: {assignees}"
            assert member_id in assignees, f"Задача {tid}: member пропал из assignees: {assignees}"


@allure.parent_suite("Multiaction")
@allure.suite("Assignees")
@allure.sub_suite("Positive")
@allure.title("Mixed state: add assignee — часть задач уже с ним")
def test_add_assignee_mixed_state(owner_client, main_space, make_task_in_main, main_personal):
    """
    Часть задач уже с assignee, часть без.
    Add assignee: изменённые в success, совпадающие в skipped.
    """
    assignee_id = main_personal["owner"][0]

    with allure.step("Создаём 2 задачи без assignee и 1 с assignee"):
        without = [make_task_in_main({"name": f"mixed-assign-{i}"}) for i in range(2)]
        with_assignee = [make_task_in_main({"name": "mixed-assign-existing", "assignees": [assignee_id]})]
        without_ids = [t["_id"] for t in without]
        with_ids = [t["_id"] for t in with_assignee]
        all_ids = without_ids + with_ids

    with allure.step("Добавляем assignee через MultipleEditTasks"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=all_ids,
            assignees=[assignee_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задачи без assignee в success"):
        assert sorted(payload["success"]) == sorted(without_ids), (
            f"Ожидали success={without_ids}, получили: {payload['success']}"
        )

    with allure.step("Проверяем, что задачи с assignee в skipped"):
        assert sorted(payload["skipped"]) == sorted(with_ids), (
            f"Ожидали skipped={with_ids}, получили: {payload['skipped']}"
        )

    with allure.step("Проверяем, что failed пуст"):
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что у всех задач assignee назначен"):
        for tid in all_ids:
            assignees = _get_task_assignees(owner_client, main_space, tid)
            assert assignee_id in assignees, (
                f"Задача {tid}: ожидали {assignee_id} в assignees, получили: {assignees}"
            )
