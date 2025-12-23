import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import multiple_edit_tasks_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Multiple Edit Tasks")
def test_multiple_edit_tasks_limit(owner_client, main_space, create_30_tasks):
    allure.dynamic.title("Multiple Edit Tasks: Проверка установленного лимита в 21 задачу — ожидаем 400 или TooManyTasksSelected")
    with allure.step("Создаём 21 задачу"):
        task_ids = create_30_tasks(count=21)
        assert len(task_ids) == 21, f"Ожидали создать 21 задачу, создано: {len(task_ids)}"

    with allure.step("Вызываем multiple_edit_tasks для 21 задачи"):
        payload_true = [{"taskId": tid} for tid in task_ids]
        resp_true = owner_client.post(**multiple_edit_tasks_endpoint(space_id=main_space, tasks=payload_true))
        body_true = resp_true.json() if resp_true.content else {}

    with allure.step("Проверяем, что пришёл 400 или error.code=TooManyTasksSelected"):
        err = (body_true.get("error") or {}) if body_true else {}
        assert (resp_true.status_code == 400) or (err.get("code") == "TooManyTasksSelected"), (
            f"Ожидали 400 или error.code=TooManyTasksSelected при 21 задаче. "
            f"status={resp_true.status_code}, error={err!r}"
        )