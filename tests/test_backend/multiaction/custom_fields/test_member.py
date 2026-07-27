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
@allure.sub_suite("Member")
@allure.title("Member add: добавить валидного мембера")
def test_member_add(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
    member_field_id, owner_member_id,
):
    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "cf-mem-add", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Добавляем мембера через multiaction [member_id, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=member_field_id,
            value=[owner_member_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id]
        assert payload["failed"] == []
        assert payload["skipped"] == []

    with allure.step("Проверяем через GetTask, что мембер добавлен"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        cf_value = _get_cf_value(r.json()["payload"]["task"], member_field_id)
        assert owner_member_id in cf_value


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Member")
@allure.title("Member add: добавить второго мембера — первый сохраняется")
def test_member_add_second(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
    member_field_id, owner_member_id, second_member_id,
):
    with allure.step("Создаём задачу и добавляем первого мембера"):
        task = make_task_in_main({"name": "cf-mem-two", "board": temp_board_in_main})
        task_id = task["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=member_field_id, value=[owner_member_id],
        ))

    with allure.step("Добавляем второго мембера через multiaction"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=member_field_id,
            value=[second_member_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id]

    with allure.step("Проверяем через GetTask, что оба мембера присутствуют"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        cf_value = _get_cf_value(r.json()["payload"]["task"], member_field_id)
        assert owner_member_id in cf_value
        assert second_member_id in cf_value


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Member")
@allure.title("Member add: мембер уже есть → skipped")
def test_member_add_already_exists_skipped(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
    member_field_id, owner_member_id,
):
    with allure.step("Создаём задачу и добавляем мембера"):
        task = make_task_in_main({"name": "cf-mem-dup", "board": temp_board_in_main})
        task_id = task["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=member_field_id, value=[owner_member_id],
        ))

    with allure.step("Пытаемся добавить того же мембера повторно"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=member_field_id,
            value=[owner_member_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Member")
@allure.title("Member remove: убрать мембера")
def test_member_remove(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
    member_field_id, owner_member_id,
):
    with allure.step("Создаём задачу и добавляем мембера"):
        task = make_task_in_main({"name": "cf-mem-rm", "board": temp_board_in_main})
        task_id = task["_id"]
        owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id,
            field_id=member_field_id, value=[owner_member_id],
        ))

    with allure.step("Удаляем мембера через multiaction [member_id, 'remove']"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=member_field_id,
            value=[owner_member_id, "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в success"):
        assert payload["success"] == [task_id]

    with allure.step("Проверяем через GetTask, что мембер убран"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        cf_value = _get_cf_value(r.json()["payload"]["task"], member_field_id)
        assert cf_value is None or owner_member_id not in cf_value


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Member")
@allure.title("Member remove: мембера нет в поле → skipped")
def test_member_remove_not_exists_skipped(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
    member_field_id, owner_member_id,
):
    with allure.step("Создаём задачу без мемберов"):
        task = make_task_in_main({"name": "cf-mem-rm-skip", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Пытаемся удалить мембера, которого нет"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=member_field_id,
            value=[owner_member_id, "remove"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []
