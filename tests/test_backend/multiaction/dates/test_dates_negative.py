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


DUE_START_LATE = _future_date(30)   # позже чем DUE_END_EARLY
DUE_END_EARLY = _future_date(5)     # раньше чем DUE_START_LATE
DUE_END_A = _future_date(15)
DUE_START_A = _future_date(5)


@allure.parent_suite("Multiaction")
@allure.suite("Dates")
@allure.sub_suite("Negative")
@allure.title("dueStart позже dueEnd — валидации нет (internal API)")
def test_due_start_after_due_end(owner_client, main_space, make_task_in_main):
    """
    Передаём dueStart позже dueEnd.
    В EditTask это 400 InvalidForm, но multiaction — internal API,
    валидация порядка дат не применяется (будет в public API).
    Ожидаем 200 + success.
    """
    with allure.step("Создаём задачу без дат"):
        task = make_task_in_main({"name": "date-order"})
        task_id = task["_id"]

    with allure.step("Применяем MultipleEditTasks: dueStart > dueEnd"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            due_start=DUE_START_LATE,
            due_end=DUE_END_EARLY,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success (валидации нет)"):
        assert payload["success"] == [task_id], (
            f"Ожидали success=[{task_id}], получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что даты сохранились в обратном порядке"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        task_data = r.json()["payload"]["task"]
        assert task_data["dueStart"].startswith(DUE_START_LATE[:10]), (
            f"dueStart не установлен: ожидали {DUE_START_LATE[:10]}, получили {task_data.get('dueStart')}"
        )
        assert task_data["dueEnd"].startswith(DUE_END_EARLY[:10]), (
            f"dueEnd не установлен: ожидали {DUE_END_EARLY[:10]}, получили {task_data.get('dueEnd')}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Dates")
@allure.sub_suite("Negative")
@allure.title("Нельзя сбросить дату через multiaction")
def test_cannot_clear_date_via_multiaction(owner_client, main_space, make_task_in_main):
    """
    Создаём задачу с dueEnd, затем вызываем multiaction без dueEnd (передаём только dueStart).
    dueStart должен установиться, а dueEnd — остаться прежним.
    """
    with allure.step("Создаём задачу с dueEnd"):
        task = make_task_in_main({"name": "date-clear", "due_end": DUE_END_A})
        task_id = task["_id"]
        stored_due_end = task["dueEnd"]

    with allure.step("Вызываем MultipleEditTasks без dueEnd (передаём только dueStart)"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            due_start=DUE_START_A,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача обработана"):
        assert task_id in payload["success"] or task_id in payload["skipped"], (
            f"Задача {task_id} не в success и не в skipped: {payload}"
        )

    with allure.step("Проверяем через GetTask: dueStart установлен, dueEnd не очистился"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        task_data = r.json()["payload"]["task"]
        assert task_data["dueStart"].startswith(DUE_START_A[:10]), (
            f"dueStart не установлен: ожидали {DUE_START_A[:10]}, получили {task_data.get('dueStart')}"
        )
        assert task_data["dueEnd"] == stored_due_end, (
            f"dueEnd изменился! Было {stored_due_end}, стало {task_data.get('dueEnd')}"
        )
