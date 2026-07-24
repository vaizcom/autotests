from datetime import datetime, timedelta

import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint

pytestmark = [pytest.mark.backend]


def _future_date(days: int) -> str:
    """Возвращает дату UTC +N дней в формате API."""
    dt = datetime.utcnow() + timedelta(days=days)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"


DUE_START_A = _future_date(5)
DUE_START_B = _future_date(10)
DUE_END_A = _future_date(15)
DUE_END_B = _future_date(20)


@allure.parent_suite("Multiaction")
@allure.suite("Dates")
@allure.sub_suite("Positive")
@allure.title("Установить dueEnd на задачах без дат")
def test_set_due_end(owner_client, main_space, make_task_in_main):
    """
    Задачи без дат, устанавливаем dueEnd.
    Все задачи в success, GetTask подтверждает.
    """
    with allure.step("Создаём 2 задачи без дат"):
        tasks = [make_task_in_main({"name": f"date-end-{i}"}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Применяем MultipleEditTasks dueEnd"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            due_end=DUE_END_A,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids)
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что dueEnd установлен"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["dueEnd"] is not None, f"dueEnd не установлен у задачи {tid}"
            assert task["dueEnd"].startswith(DUE_END_A[:19]), (
                f"Задача {tid}: ожидали dueEnd начинающийся с {DUE_END_A[:19]}, получили {task['dueEnd']}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Dates")
@allure.sub_suite("Positive")
@allure.title("Установить только dueStart — dueEnd не трогается")
def test_set_due_start_only(owner_client, main_space, make_task_in_main):
    """
    Задачи с dueEnd, устанавливаем только dueStart.
    dueEnd не должен измениться.
    """
    with allure.step("Создаём 2 задачи с dueEnd, без dueStart"):
        tasks = [make_task_in_main({"name": f"date-start-{i}", "due_end": DUE_END_A}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]
        original_due_ends = {t["_id"]: t.get("dueEnd") for t in tasks}

    with allure.step("Применяем MultipleEditTasks только dueStart"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            due_start=DUE_START_A,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids)
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask: dueStart установлен, dueEnd не изменился"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["dueStart"].startswith(DUE_START_A[:19]), (
                f"Задача {tid}: dueStart не установлен, получили {task.get('dueStart')}"
            )
            assert task["dueEnd"] == original_due_ends[tid], (
                f"Задача {tid}: dueEnd изменился! Было {original_due_ends[tid]}, стало {task.get('dueEnd')}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Dates")
@allure.sub_suite("Positive")
@allure.title("Установить оба поля: dueStart и dueEnd")
def test_set_both_dates(owner_client, main_space, make_task_in_main):
    """
    Задачи без дат, устанавливаем dueStart и dueEnd одновременно.
    Оба поля обновляются в одном запросе.
    """
    with allure.step("Создаём 2 задачи без дат"):
        tasks = [make_task_in_main({"name": f"date-both-{i}"}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Применяем MultipleEditTasks dueStart + dueEnd"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=task_ids,
            due_start=DUE_START_A,
            due_end=DUE_END_A,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids)
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask: оба поля установлены"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["dueStart"].startswith(DUE_START_A[:19]), (
                f"Задача {tid}: dueStart не установлен, получили {task.get('dueStart')}"
            )
            assert task["dueEnd"].startswith(DUE_END_A[:19]), (
                f"Задача {tid}: dueEnd не установлен, получили {task.get('dueEnd')}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Dates")
@allure.sub_suite("Positive")
@allure.title("dueEnd совпадает с текущим значением → задача в skipped")
def test_due_end_same_value_skipped(owner_client, main_space, make_task_in_main):
    """
    dueEnd совпадает с текущим значением задачи.
    Задача попадает в skipped (значение не изменилось).
    """
    with allure.step("Создаём задачу с dueEnd"):
        task = make_task_in_main({"name": "date-skip", "due_end": DUE_END_A})
        task_id = task["_id"]
        stored_due_end = task["dueEnd"]

    with allure.step("Применяем MultipleEditTasks с тем же dueEnd"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            due_end=stored_due_end,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id], (
            f"Ожидали skipped=[{task_id}], получили: {payload['skipped']}"
        )
        assert payload["success"] == [], f"success не пуст: {payload['success']}"
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что dueEnd не изменился"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        task_data = r.json()["payload"]["task"]
        assert task_data["dueEnd"] == stored_due_end, (
            f"dueEnd изменился! Было {stored_due_end}, стало {task_data.get('dueEnd')}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Dates")
@allure.sub_suite("Positive")
@allure.title("Mixed: dueStart совпадает у части задач → partial skipped/success")
def test_mixed_due_start_partial_match(owner_client, main_space, make_task_in_main):
    """
    Часть задач уже с dueStart=A, часть без.
    Применяем dueStart=A: совпадающие в skipped, остальные в success.
    """
    with allure.step("Создаём 2 задачи без dueStart и 1 с dueStart"):
        different = [make_task_in_main({"name": f"mixed-no-start-{i}"}) for i in range(2)]
        same = [make_task_in_main({"name": "mixed-has-start", "due_start": DUE_START_A})]
        diff_ids = [t["_id"] for t in different]
        same_ids = [t["_id"] for t in same]
        stored_due_start = same[0]["dueStart"]
        all_ids = diff_ids + same_ids

    with allure.step("Применяем MultipleEditTasks dueStart с тем же значением"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=all_ids,
            due_start=stored_due_start,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задачи без dueStart в success"):
        assert sorted(payload["success"]) == sorted(diff_ids), (
            f"Ожидали success={diff_ids}, получили: {payload['success']}"
        )

    with allure.step("Проверяем, что совпадающая задача в skipped"):
        assert sorted(payload["skipped"]) == sorted(same_ids), (
            f"Ожидали skipped={same_ids}, получили: {payload['skipped']}"
        )

    with allure.step("Проверяем, что failed пуст"):
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что dueStart установлен у всех задач"):
        for tid in all_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task_data = r.json()["payload"]["task"]
            assert task_data["dueStart"] == stored_due_start, (
                f"Задача {tid}: ожидали dueStart={stored_due_start}, получили {task_data.get('dueStart')}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Dates")
@allure.sub_suite("Positive")
@allure.title("dueStart совпадает, dueEnd отличается → success")
def test_or_logic_due_start_matches_due_end_differs(owner_client, main_space, make_task_in_main):
    """
    Задача с dueStart=A и dueEnd=A.
    Применяем dueStart=A + dueEnd=B.
    dueEnd отличается → задача в success (достаточно одного отличия).
    """
    with allure.step("Создаём задачу с dueStart=A и dueEnd=A"):
        task = make_task_in_main({
            "name": "date-partial-match",
            "due_start": DUE_START_A,
            "due_end": DUE_END_A,
        })
        task_id = task["_id"]
        stored_due_start = task["dueStart"]

    with allure.step("Применяем MultipleEditTasks: тот же dueStart, другой dueEnd"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            due_start=stored_due_start,
            due_end=DUE_END_B,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success (достаточно одного отличия)"):
        assert payload["success"] == [task_id], (
            f"Ожидали success=[{task_id}], получили: {payload['success']}"
        )
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask: dueEnd обновился, dueStart не изменился"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        task = r.json()["payload"]["task"]
        assert task["dueEnd"].startswith(DUE_END_B[:19]), (
            f"dueEnd не обновился: ожидали {DUE_END_B[:19]}, получили {task['dueEnd']}"
        )
        assert task["dueStart"].startswith(DUE_START_A[:19]), (
            f"dueStart изменился: ожидали {DUE_START_A[:19]}, получили {task['dueStart']}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Dates")
@allure.sub_suite("Positive")
@allure.title("Оба поля совпадают → все в skipped")
def test_both_dates_match_all_skipped(owner_client, main_space, make_task_in_main):
    """
    Задача с dueStart=A и dueEnd=A.
    Применяем те же значения → задача в skipped.
    """
    with allure.step("Создаём задачу с обоими датами"):
        task = make_task_in_main({
            "name": "both-skip",
            "due_start": DUE_START_A,
            "due_end": DUE_END_A,
        })
        task_id = task["_id"]
        stored_due_start = task["dueStart"]
        stored_due_end = task["dueEnd"]

    with allure.step("Применяем MultipleEditTasks с теми же датами"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            due_start=stored_due_start,
            due_end=stored_due_end,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id], (
            f"Ожидали skipped=[{task_id}], получили: {payload['skipped']}"
        )
        assert payload["success"] == [], f"success не пуст: {payload['success']}"
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"

    with allure.step("Проверяем через GetTask, что даты не изменились"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        task_data = r.json()["payload"]["task"]
        assert task_data["dueStart"] == stored_due_start, (
            f"dueStart изменился! Было {stored_due_start}, стало {task_data.get('dueStart')}"
        )
        assert task_data["dueEnd"] == stored_due_end, (
            f"dueEnd изменился! Было {stored_due_end}, стало {task_data.get('dueEnd')}"
        )
