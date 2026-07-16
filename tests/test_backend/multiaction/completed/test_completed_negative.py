import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Multiaction")
@allure.suite("Completed")
@allure.sub_suite("Negative")
@allure.title("Невалидный taskId попадает в failed, валидные — в success")
def test_mark_completed_invalid_task_id(owner_client, main_space, make_task_in_main):
    """
    Передаём валидный и несуществующий taskId.
    Валидный — в success, невалидный — в failed.
    """
    with allure.step("Создаём задачу и генерируем невалидный taskId"):
        task = make_task_in_main({"name": "valid-task", "completed": False})
        valid_id = task["_id"]
        invalid_id = valid_id[:-1] + ("0" if valid_id[-1] != "0" else "1")

    with allure.step("Применяем MultipleEditTasks completed=True"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[valid_id, invalid_id],
            completed=True,
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

    with allure.step("Проверяем, что skipped пуст"):
        assert payload["skipped"] == [], f"skipped не пуст: {payload['skipped']}"

    with allure.step("Проверяем через GetTask, что валидная задача стала completed"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=valid_id))
        assert r.status_code == 200, r.text
        assert r.json()["payload"]["task"]["completed"] is True
