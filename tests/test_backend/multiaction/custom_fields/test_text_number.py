import uuid

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
@allure.sub_suite("Text / Number")
@allure.title("Text: обновить значение у одной задачи")
def test_text_single_task(
    owner_client, main_space, make_task_in_main, temp_board_in_main, text_field_id,
):
    new_value = f"val-{uuid.uuid4().hex[:6]}"

    with allure.step("Создаём задачу на temp борде"):
        task = make_task_in_main({"name": "cf-text-1", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Применяем MultipleEditTasksCustomField"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=text_field_id, value=new_value,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id]
        assert payload["failed"] == []
        assert payload["skipped"] == []

    with allure.step("Проверяем через GetTask"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        assert _get_cf_value(r.json()["payload"]["task"], text_field_id) == new_value


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Text / Number")
@allure.title("Number: обновить значение у нескольких задач")
def test_number_multiple_tasks(
    owner_client, main_space, make_task_in_main, temp_board_in_main, number_field_id,
):
    new_value = "42"

    with allure.step("Создаём 3 задачи на temp борде"):
        tasks = [make_task_in_main({"name": f"cf-num-{i}", "board": temp_board_in_main}) for i in range(3)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Применяем MultipleEditTasksCustomField"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=task_ids,
            custom_field_id=number_field_id, value=new_value,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids)
        assert payload["failed"] == []
        assert payload["skipped"] == []

    with allure.step("Проверяем через GetTask"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            assert _get_cf_value(r.json()["payload"]["task"], number_field_id) == new_value


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Text / Number")
@allure.title("Значение уже совпадает → задача в skipped")
def test_text_same_value_skipped(
    owner_client, main_space, make_task_in_main, temp_board_in_main, text_field_id,
):
    value = f"same-{uuid.uuid4().hex[:6]}"

    with allure.step("Создаём задачу и устанавливаем значение"):
        task = make_task_in_main({"name": "cf-same", "board": temp_board_in_main})
        task_id = task["_id"]
        r = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id, field_id=text_field_id, value=value,
        ))
        assert r.status_code == 200, r.text

    with allure.step("Применяем MultipleEditTasksCustomField с тем же значением"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=text_field_id, value=value,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []
        assert payload["failed"] == []

    with allure.step("Проверяем через GetTask, что значение не изменилось"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        assert _get_cf_value(r.json()["payload"]["task"], text_field_id) == value
