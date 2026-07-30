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
@allure.sub_suite("Base logic")
@allure.title("Очистка: value=null → 400 InvalidForm")
def test_clear_value_null_rejected(
    owner_client, main_space, make_task_in_main, temp_board_in_main, text_field_id,
):
    """Общая логика для всех типов (Text, Number, Checkbox, Date, Select, Member, TaskRelations, Url, Estimation).
    API не поддерживает очистку через value=null."""
    with allure.step("Создаём задачу и устанавливаем значение"):
        task = make_task_in_main({"name": "cf-clear", "board": temp_board_in_main})
        task_id = task["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id, field_id=text_field_id, value="to-clear",
        ))

    with allure.step("Передаём value=None"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=text_field_id, value=None,
        ))

    with allure.step("Проверяем, что API возвращает 400"):
        assert resp.status_code == 400, f"Ожидали 400, получили {resp.status_code}"
        error = resp.json().get("error", {})
        assert error.get("code") == "InvalidForm"


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Base logic")
@allure.title("Поле не определено на борде → все в skipped")
def test_field_not_on_board_all_skipped(
    owner_client, main_space, make_task_in_main, text_field_id,
):
    """Общая логика для всех типов (Text, Number, Checkbox, Date, Select, Member, TaskRelations, Url, Estimation).
    Поле определено на temp_board, задача на main_board — тип поля не влияет."""
    with allure.step("Создаём задачу на main борде (без кастом филда)"):
        task = make_task_in_main({"name": "cf-no-board"})
        task_id = task["_id"]

    with allure.step("Применяем multiaction с полем от другой борды"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=text_field_id, value="should-skip",
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []
        assert payload["failed"] == []

    with allure.step("Проверяем через GetTask, что поле не появилось"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        assert _get_cf_value(r.json()["payload"]["task"], text_field_id) is None


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Base logic")
@allure.title("Mixed: часть задач уже с тем же значением → partial skipped/success")
def test_mixed_some_match(
    owner_client, main_space, make_task_in_main, temp_board_in_main, number_field_id,
):
    target_value = "99"

    with allure.step("Создаём задачу с другим значением и задачу с тем же"):
        task_diff = make_task_in_main({"name": "cf-mix-diff", "board": temp_board_in_main})
        task_same = make_task_in_main({"name": "cf-mix-same", "board": temp_board_in_main})
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_same["_id"],
            field_id=number_field_id, value=target_value,
        ))

    with allure.step("Применяем multiaction"):
        all_ids = [task_diff["_id"], task_same["_id"]]
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=all_ids,
            custom_field_id=number_field_id, value=target_value,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем: изменённая в success, совпадающая в skipped"):
        assert payload["success"] == [task_diff["_id"]]
        assert payload["skipped"] == [task_same["_id"]]
        assert payload["failed"] == []


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Base logic")
@allure.title("Задачи с разных бордов: поле есть на одной, нет на другой")
def test_mixed_different_boards(
    owner_client, main_space, make_task_in_main, temp_board_in_main, text_field_id,
):
    new_value = f"cross-{uuid.uuid4().hex[:6]}"

    with allure.step("Создаём задачу на temp борде и задачу на main борде"):
        task_temp = make_task_in_main({"name": "cf-cross-temp", "board": temp_board_in_main})
        task_main = make_task_in_main({"name": "cf-cross-main"})

    with allure.step("Применяем multiaction с полем от temp борды"):
        all_ids = [task_temp["_id"], task_main["_id"]]
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=all_ids,
            custom_field_id=text_field_id, value=new_value,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем: temp задача в success, main задача в skipped"):
        assert task_temp["_id"] in payload["success"], (
            f"Задача temp борды не в success: {payload}"
        )
        assert task_main["_id"] in payload["skipped"], (
            f"Задача main борды не в skipped: {payload}"
        )
