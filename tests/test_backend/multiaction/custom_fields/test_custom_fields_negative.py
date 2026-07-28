import allure
import pytest

from config.generators import generate_object_id
from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_custom_field_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Negative")
@allure.title("customFieldId не существует ни на одном борде → все в skipped")
def test_field_not_on_any_board(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
):
    fake_field_id = generate_object_id()

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "cf-neg-fake", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Применяем multiaction с несуществующим customFieldId"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=fake_field_id, value="anything",
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id], (
            f"Ожидали skipped=[{task_id}], получили: {payload}"
        )
        assert payload["success"] == []
        assert payload["failed"] == []


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Negative")
@allure.title("Операция add/remove для поля Text → failed")
def test_tuple_for_scalar_field(
    owner_client, main_space, make_task_in_main, temp_board_in_main, text_field_id,
):
    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "cf-neg-tuple", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Передаём [id, 'add'] для Text поля"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=text_field_id, value=["some-value", "add"],
        ))

    with allure.step("Проверяем ответ"):
        if resp.status_code == 400:
            error = resp.json().get("error", {})
            assert error.get("code"), "Ожидали error.code в ответе 400"
        else:
            payload = assert_multiaction_response(resp)
            assert payload["failed"] == [task_id], (
                f"Ожидали failed=[{task_id}], получили: {payload}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Negative")
@allure.title("Select add: невалидная опция → все в failed")
def test_select_invalid_option(
    owner_client, main_space, make_task_in_main, temp_board_in_main, select_field,
):
    fake_option_id = generate_object_id()

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "cf-neg-sel", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Добавляем несуществующую опцию [fake_id, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=select_field["field_id"],
            value=[fake_option_id, "add"],
        ))

    with allure.step("Проверяем ответ"):
        if resp.status_code == 400:
            error = resp.json().get("error", {})
            assert error.get("code"), "Ожидали error.code в ответе 400"
        else:
            payload = assert_multiaction_response(resp)
            assert payload["failed"] == [task_id], (
                f"Ожидали failed=[{task_id}], получили: {payload}"
            )


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Negative")
@allure.title("Member add: несуществующий member ID → success (API не валидирует)")
def test_member_invalid_id(
    owner_client, main_space, make_task_in_main, temp_board_in_main, member_field_id,
):
    """API не проверяет существование мембера — принимает любой ObjectId, т.е.
    нет проверки существования memberId в БД — только проверка формата mongoId"""

    fake_member_id = generate_object_id()

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "cf-neg-mem", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Добавляем несуществующего мембера [fake_id, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=member_field_id,
            value=[fake_member_id, "add"],
        ))

    with allure.step("Проверяем, что API принимает без валидации"):
        payload = assert_multiaction_response(resp)
        assert payload["success"] == [task_id]


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Negative")
@allure.title("Нет доступа к спейсу → ошибка")
def test_no_access_to_space(
    foreign_client, main_space, make_task_in_main, temp_board_in_main, text_field_id,
):
    """foreign_client не имеет доступа к main_space."""
    with allure.step("Создаём задачу (от owner)"):
        task = make_task_in_main({"name": "cf-neg-access", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Применяем multiaction от foreign_client"):
        resp = foreign_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=text_field_id, value="hacked",
        ))

    with allure.step("Проверяем, что доступ запрещён"):
        assert resp.status_code in (400, 403), (
            f"Ожидали 400 или 403, получили {resp.status_code}"
        )
        error_code = resp.json().get("error", {}).get("code", "")
        assert error_code in ("AccessDenied", "SpaceIdNotSpecified"), (
            f"Ожидали AccessDenied или SpaceIdNotSpecified, получили: {error_code}"
        )
