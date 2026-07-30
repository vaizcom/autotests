import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_custom_field_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint, edit_task_custom_field_endpoint

pytestmark = [pytest.mark.backend]


def _get_cf_value(task, field_id):
    for cf in task.get("customFields", []):
        if cf.get("id") == field_id:
            return cf.get("value")
    return None


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Linked Tasks")
@allure.title("Linked Tasks add: привязать задачу")
def test_linked_tasks_add(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
    linked_tasks_field_id,
):
    with allure.step("Создаём две задачи: основную и связываемую"):
        task = make_task_in_main({"name": "cf-link-main", "board": temp_board_in_main})
        task_id = task["_id"]
        linked = make_task_in_main({"name": "cf-link-target", "board": temp_board_in_main})
        linked_id = linked["_id"]

    with allure.step("Привязываем задачу через multiaction [linked_id, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=linked_tasks_field_id,
            value=[linked_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id]
        assert payload["failed"] == []
        assert payload["skipped"] == []

    with allure.step("Проверяем через GetTask, что связь создана"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        cf_value = _get_cf_value(r.json()["payload"]["task"], linked_tasks_field_id)
        assert linked_id in cf_value


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Linked Tasks")
@allure.title("Linked Tasks remove: отвязать задачу")
def test_linked_tasks_remove(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
    linked_tasks_field_id,
):
    with allure.step("Создаём две задачи и привязываем"):
        task = make_task_in_main({"name": "cf-unlink-main", "board": temp_board_in_main})
        task_id = task["_id"]
        linked = make_task_in_main({"name": "cf-unlink-target", "board": temp_board_in_main})
        linked_id = linked["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=linked_tasks_field_id, value=[linked_id],
        ))

    with allure.step("Отвязываем через multiaction [linked_id, 'remove']"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=linked_tasks_field_id,
            value=[linked_id, "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id]

    with allure.step("Проверяем через GetTask, что связь убрана"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        cf_value = _get_cf_value(r.json()["payload"]["task"], linked_tasks_field_id)
        assert cf_value is None or linked_id not in cf_value


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Linked Tasks")
@allure.title("Linked Tasks add: добавить вторую связь — первая сохраняется")
def test_linked_tasks_add_second(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
    linked_tasks_field_id,
):
    with allure.step("Создаём три задачи: основную и две связываемые"):
        task = make_task_in_main({"name": "cf-link-two", "board": temp_board_in_main})
        task_id = task["_id"]
        linked_1 = make_task_in_main({"name": "cf-link-t1", "board": temp_board_in_main})
        linked_1_id = linked_1["_id"]
        linked_2 = make_task_in_main({"name": "cf-link-t2", "board": temp_board_in_main})
        linked_2_id = linked_2["_id"]

    with allure.step("Привязываем первую задачу"):
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=linked_tasks_field_id, value=[linked_1_id],
        ))

    with allure.step("Добавляем вторую через multiaction"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=linked_tasks_field_id,
            value=[linked_2_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id]

    with allure.step("Проверяем через GetTask, что обе связи присутствуют"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        cf_value = _get_cf_value(r.json()["payload"]["task"], linked_tasks_field_id)
        assert linked_1_id in cf_value
        assert linked_2_id in cf_value


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Linked Tasks")
@allure.title("Linked Tasks add: связь уже есть → skipped")
def test_linked_tasks_add_already_exists_skipped(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
    linked_tasks_field_id,
):
    with allure.step("Создаём две задачи и привязываем"):
        task = make_task_in_main({"name": "cf-link-dup", "board": temp_board_in_main})
        task_id = task["_id"]
        linked = make_task_in_main({"name": "cf-link-dup-t", "board": temp_board_in_main})
        linked_id = linked["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=linked_tasks_field_id, value=[linked_id],
        ))

    with allure.step("Пытаемся привязать ту же задачу повторно"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=linked_tasks_field_id,
            value=[linked_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Linked Tasks")
@allure.title("Linked Tasks remove: связи нет → skipped")
def test_linked_tasks_remove_not_exists_skipped(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
    linked_tasks_field_id,
):
    with allure.step("Создаём две задачи без связи"):
        task = make_task_in_main({"name": "cf-link-rm-skip", "board": temp_board_in_main})
        task_id = task["_id"]
        other = make_task_in_main({"name": "cf-link-rm-skip-t", "board": temp_board_in_main})
        other_id = other["_id"]

    with allure.step("Пытаемся отвязать задачу, которой нет в поле"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=linked_tasks_field_id,
            value=[other_id, "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []
