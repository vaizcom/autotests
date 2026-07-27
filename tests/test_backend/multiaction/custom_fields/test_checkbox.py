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
@allure.sub_suite("Checkbox")
@allure.title("Checkbox: установить true")
def test_checkbox_set_true(
    owner_client, main_space, make_task_in_main, temp_board_in_main, checkbox_field_id,
):
    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "cf-chk-true", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Устанавливаем Boolean = true через multiaction"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=checkbox_field_id, value=True,
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
        assert _get_cf_value(r.json()["payload"]["task"], checkbox_field_id) is True


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Checkbox")
@allure.title("Checkbox: значение совпадает → skipped")
def test_checkbox_same_value_skipped(
    owner_client, main_space, make_task_in_main, temp_board_in_main, checkbox_field_id,
):
    with allure.step("Создаём задачу и устанавливаем Boolean = false"):
        task = make_task_in_main({"name": "cf-chk-skip", "board": temp_board_in_main})
        task_id = task["_id"]
        r = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id, field_id=checkbox_field_id, value=False,
        ))
        assert r.status_code == 200, r.text

    with allure.step("Применяем multiaction с тем же значением false"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=checkbox_field_id, value=False,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []
