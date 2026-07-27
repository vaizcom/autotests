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
@allure.sub_suite("Select")
@allure.title("Select add: элемента нет в массиве → добавляется")
def test_select_add_element(
    owner_client, main_space, make_task_in_main, temp_board_in_main, select_field,
):
    with allure.step("Создаём задачу и устанавливаем option_b"):
        task = make_task_in_main({"name": "cf-sel-add", "board": temp_board_in_main})
        task_id = task["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=select_field["field_id"], value=[select_field["option_b"]],
        ))

    with allure.step("Добавляем option_a через multiaction [option_a, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=select_field["field_id"],
            value=[select_field["option_a"], "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id]

    with allure.step("Проверяем через GetTask, что обе опции присутствуют"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        cf_value = _get_cf_value(r.json()["payload"]["task"], select_field["field_id"])
        assert select_field["option_a"] in cf_value
        assert select_field["option_b"] in cf_value


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Select")
@allure.title("Select: замена одной опции на другую (remove + add)")
def test_select_replace_option(
    owner_client, main_space, make_task_in_main, temp_board_in_main, select_field,
):
    with allure.step("Создаём задачу с option_a"):
        task = make_task_in_main({"name": "cf-sel-replace", "board": temp_board_in_main})
        task_id = task["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=select_field["field_id"], value=[select_field["option_a"]],
        ))

    with allure.step("Удаляем option_a через multiaction"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=select_field["field_id"],
            value=[select_field["option_a"], "remove"],
        ))
        payload = assert_multiaction_response(resp)
        assert payload["success"] == [task_id]

    with allure.step("Добавляем option_b через multiaction"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=select_field["field_id"],
            value=[select_field["option_b"], "add"],
        ))
        payload = assert_multiaction_response(resp)
        assert payload["success"] == [task_id]

    with allure.step("Проверяем через GetTask: только option_b"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        cf_value = _get_cf_value(r.json()["payload"]["task"], select_field["field_id"])
        assert cf_value == [select_field["option_b"]]


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Select")
@allure.title("Select add: элемент уже есть → skipped")
def test_select_add_already_exists_skipped(
    owner_client, main_space, make_task_in_main, temp_board_in_main, select_field,
):
    with allure.step("Создаём задачу и устанавливаем option_a"):
        task = make_task_in_main({"name": "cf-sel-dup", "board": temp_board_in_main})
        task_id = task["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=select_field["field_id"], value=[select_field["option_a"]],
        ))

    with allure.step("Пытаемся добавить option_a повторно"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=select_field["field_id"],
            value=[select_field["option_a"], "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Select")
@allure.title("Select remove: элемент есть → убирается")
def test_select_remove_element(
    owner_client, main_space, make_task_in_main, temp_board_in_main, select_field,
):
    with allure.step("Создаём задачу и устанавливаем обе опции"):
        task = make_task_in_main({"name": "cf-sel-rm", "board": temp_board_in_main})
        task_id = task["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=select_field["field_id"],
            value=[select_field["option_a"], select_field["option_b"]],
        ))

    with allure.step("Удаляем option_a через multiaction [option_a, 'remove']"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=select_field["field_id"],
            value=[select_field["option_a"], "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id]

    with allure.step("Проверяем через GetTask, что option_a убрана, option_b осталась"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        cf_value = _get_cf_value(r.json()["payload"]["task"], select_field["field_id"])
        assert select_field["option_a"] not in cf_value
        assert select_field["option_b"] in cf_value


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Select")
@allure.title("Select remove: элемента нет → skipped")
def test_select_remove_not_exists_skipped(
    owner_client, main_space, make_task_in_main, temp_board_in_main, select_field,
):
    with allure.step("Создаём задачу и устанавливаем только option_b"):
        task = make_task_in_main({"name": "cf-sel-rm-skip", "board": temp_board_in_main})
        task_id = task["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=select_field["field_id"], value=[select_field["option_b"]],
        ))

    with allure.step("Пытаемся удалить option_a (которого нет)"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=select_field["field_id"],
            value=[select_field["option_a"], "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []
