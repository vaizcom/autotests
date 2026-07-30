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
@allure.sub_suite("Negative")
@allure.title("Add member_id не из спейса — принимается без валидации")
def test_add_invalid_member_id(owner_client, main_space, make_task_in_main):
    """
    Передаём несуществующий member_id (не в спейсе) с action=add.
    MultipleEditTasks не валидирует принадлежность к спейсу — ожидаемое поведение,
    т.к. валидация на каждый member тяжёлая операция для массового эндпоинта.
    EditTask валидирует (400) — это исключение, сделано для МСП.
    Фронт отображает такого пользователя как "missing member".
    """
    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "invalid-assignee"})
        task_id = task["_id"]

    invalid_member_id = "000000000000000000000000"

    with allure.step("Применяем MultipleEditTasks assignees=[invalid_id, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            assignees=[invalid_member_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        assert resp.status_code == 200, f"Неожиданный статус: {resp.status_code}"
        payload = assert_multiaction_response(resp)
        # API не валидирует member_id — задача попадает в success
        assert payload["success"] == [task_id], (
            f"Ожидали success=[{task_id}], получили: {payload['success']}"
        )

    with allure.step("BUG: невалидный member_id записан в assignees"):
        assignees = _get_task_assignees(owner_client, main_space, task_id)
        # Фиксируем баг: API записывает несуществующий member_id
        assert invalid_member_id in assignees, (
            f"Поведение изменилось — невалидный member_id больше не в assignees: {assignees}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Assignees")
@allure.sub_suite("Negative")
@allure.title("Remove assignee, которого нет на задаче")
def test_remove_absent_assignee(owner_client, main_space, make_task_in_main, main_personal):
    """
    Задача без assignees, пытаемся remove.
    Ожидаем skipped.
    """
    assignee_id = main_personal["owner"][0]

    with allure.step("Создаём задачу без assignees"):
        task = make_task_in_main({"name": "remove-absent-assignee"})
        task_id = task["_id"]

    with allure.step("Пытаемся remove assignee, которого нет"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            assignees=[assignee_id, "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert task_id in payload["skipped"], (
            f"Ожидали задачу в skipped, получили: success={payload['success']}"
        )

    with allure.step("Проверяем, что assignees по-прежнему пуст"):
        assignees = _get_task_assignees(owner_client, main_space, task_id)
        assert assignees == [], f"assignees не пуст: {assignees}"


@allure.parent_suite("Multiaction")
@allure.suite("Assignees")
@allure.sub_suite("Negative")
@allure.title("Невалидный taskId + add assignee")
def test_add_assignee_invalid_task_id(owner_client, main_space, make_task_in_main, main_personal):
    """
    Передаём валидный и несуществующий taskId с assignee add.
    Валидный — в success, невалидный — в failed.
    """
    assignee_id = main_personal["owner"][0]

    with allure.step("Создаём задачу и генерируем невалидный taskId"):
        task = make_task_in_main({"name": "valid-assignee-task"})
        valid_id = task["_id"]
        invalid_id = valid_id[:-1] + ("0" if valid_id[-1] != "0" else "1")

    with allure.step("Применяем MultipleEditTasks assignees add"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[valid_id, invalid_id],
            assignees=[assignee_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что валидный taskId в success"):
        assert payload["success"] == [valid_id], (
            f"Ожидали success=[{valid_id}], получили: {payload['success']}"
        )

    with allure.step("Проверяем, что невалидный taskId в failed"):
        assert payload["failed"] == [invalid_id], (
            f"Ожидали failed=[{invalid_id}], получили: {payload['failed']}"
        )

    with allure.step("Проверяем через GetTask, что assignee назначен"):
        assignees = _get_task_assignees(owner_client, main_space, valid_id)
        assert assignee_id in assignees, (
            f"assignee не назначен на валидную задачу: {assignees}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Assignees")
@allure.sub_suite("Negative")
@allure.title("Два member_id в одном запросе")
def test_two_member_ids_in_single_request(owner_client, main_space, make_task_in_main, main_personal):
    """
    Передаём ["id1", "id2", "add"] — два member_id в одном запросе.
    Формат предполагает [memberId, action], длина массива != 2 → 400.
    """
    owner_id = main_personal["owner"][0]
    member_id = main_personal["member"][0]

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "two-ids-one-request"})
        task_id = task["_id"]

    with allure.step("Отправляем assignees=[id1, id2, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            assignees=[owner_id, member_id, "add"],
        ))

    with allure.step("Проверяем, что API отклонил невалидный формат"):
        assert resp.status_code == 400, (
            f"Ожидали 400 для массива длиной != 2, получили: {resp.status_code}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Assignees")
@allure.sub_suite("Negative")
@allure.title("Допустимые action только 'add' и 'remove' — 'toggle' отклоняется")
def test_invalid_action_toggle(owner_client, main_space, make_task_in_main, main_personal):
    """
    assignees принимает только [memberId, 'add'] или [memberId, 'remove'].
    Любой другой action (например 'toggle') → 400.
    """
    assignee_id = main_personal["owner"][0]

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "toggle-action"})
        task_id = task["_id"]

    with allure.step("Отправляем assignees=[id, 'toggle']"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            assignees=[assignee_id, "toggle"],
        ))

    with allure.step("Проверяем, что API отклонил запрос"):
        assert resp.status_code == 400, (
            f"Ожидали 400 для невалидного action 'toggle', получили: {resp.status_code}"
        )
