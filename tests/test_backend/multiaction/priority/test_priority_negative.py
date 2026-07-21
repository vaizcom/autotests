import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.data.endpoints.Task.constants import PRIORITY_GENERAL, PRIORITY_MEDIUM

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Multiaction")
@allure.suite("Priority")
@allure.sub_suite("Negative")
@allure.title("Невалидный priority (за пределами допустимого диапазона)")
def test_set_invalid_priority(owner_client, main_space, make_task_in_main):
    """
    Передаём невалидный priority (за пределами LOW-HIGH).
    Ожидаем 400 или задачи в failed.
    """
    invalid_priority = 99

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "invalid-priority"})
        task_id = task["_id"]
        original_priority = task.get("priority", PRIORITY_GENERAL)

    with allure.step(f"Применяем MultipleEditTasks priority={invalid_priority}"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            priority=invalid_priority,
        ))

    with allure.step("Проверяем, что бэкенд отклонил запрос"):
        assert resp.status_code in (200, 400), f"Неожиданный статус: {resp.status_code}"

        if resp.status_code == 400:
            error = resp.json().get("error", {})
            assert error, "Ожидали объект error в ответе 400"
        else:
            payload = assert_multiaction_response(resp)
            assert payload["failed"] == [task_id], (
                f"Ожидали failed=[{task_id}], получили: {payload['failed']}"
            )

    with allure.step("Проверяем, что priority не изменился"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=task_id))
        assert r.status_code == 200, r.text
        task = r.json()["payload"]["task"]
        assert task["priority"] == original_priority, (
            f"Priority изменился с {original_priority} на {task['priority']} при невалидном значении!"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Priority")
@allure.sub_suite("Negative")
@allure.title("Невалидный taskId + priority: валидный в success, невалидный в failed")
def test_set_priority_invalid_task_id(owner_client, main_space, make_task_in_main):
    """
    Передаём валидный и несуществующий taskId с priority=MEDIUM.
    Валидный — в success, невалидный — в failed.
    """
    with allure.step("Создаём задачу и генерируем невалидный taskId"):
        task = make_task_in_main({"name": "valid-priority-task", "priority": PRIORITY_GENERAL})
        valid_id = task["_id"]
        invalid_id = valid_id[:-1] + ("0" if valid_id[-1] != "0" else "1")

    with allure.step("Применяем MultipleEditTasks priority=MEDIUM"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[valid_id, invalid_id],
            priority=PRIORITY_MEDIUM,
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

    with allure.step("Проверяем через GetTask, что priority=MEDIUM"):
        r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=valid_id))
        assert r.status_code == 200, r.text
        assert r.json()["payload"]["task"]["priority"] == PRIORITY_MEDIUM
