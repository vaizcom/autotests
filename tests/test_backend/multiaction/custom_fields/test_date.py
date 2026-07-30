from datetime import datetime, timedelta

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


def _iso_date(days_offset):
    """ISO 8601 дата с отступом от сегодня."""
    dt = datetime.utcnow() + timedelta(days=days_offset)
    return dt.strftime("%Y-%m-%dT00:00:00.000Z")


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Date")
@allure.title("Date: установить диапазон дат")
def test_date_set_range(
    owner_client, main_space, make_task_in_main, temp_board_in_main, date_field_id,
):
    date_start = _iso_date(10)
    date_end = _iso_date(20)
    new_value = [date_start, date_end]

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "cf-date-range", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Устанавливаем диапазон дат через multiaction"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=date_field_id, value=new_value,
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
        cf_value = _get_cf_value(r.json()["payload"]["task"], date_field_id)
        assert cf_value is not None, "Дата не установлена"


@allure.parent_suite("Multiaction")
@allure.suite("Custom Fields")
@allure.sub_suite("Date")
@allure.title("Date: значение совпадает → skipped")
def test_date_same_value_skipped(
    owner_client, main_space, make_task_in_main, temp_board_in_main, date_field_id,
):
    date_value = [_iso_date(30), _iso_date(40)]

    with allure.step("Создаём задачу и устанавливаем дату"):
        task = make_task_in_main({"name": "cf-date-skip", "board": temp_board_in_main})
        task_id = task["_id"]
        r = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space, task_id=task_id, field_id=date_field_id, value=date_value,
        ))
        assert r.status_code == 200, r.text

    with allure.step("Применяем multiaction с тем же значением"):
        resp = owner_client.post(**multiple_edit_tasks_custom_field_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            custom_field_id=date_field_id, value=date_value,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []
