import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import multiple_edit_tasks_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Task Service")
@allure.suite("Multiple Edit Tasks")
@allure.title("Multiple Edit Tasks: базовая проверка работоспособности и контракта ответа")
def test_multiple_edit_tasks_minimal_payload(owner_client, main_space):
    """
    Проверяет, что эндпоинт MultipleEditTasks принимает минимальный payload:
      { "tasks": [ { "taskId": "<id>" } ] }
    """
    task_id = "691dc3028b5dc0d953494c5b"

    with allure.step("Отправляем запрос MultipleEditTasks с минимальным payload"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(space_id=main_space, tasks=[{"taskId": task_id}]))

    with allure.step("Проверяем успешный статус и базовую структуру ответа"):
        assert resp.status_code == 200
        body = resp.json()

    with allure.step("Проверяем контракт ответа (payload.success/failed)"):
        assert body.get("type") == "MultipleEditTasks", f"Некорректный type: {body.get('type')!r}"
        payload = body.get("payload") or {}
        success = (payload.get("success") if "success" in payload else body.get("success")) or []
        failed = (payload.get("failed") if "failed" in payload else body.get("failed")) or []
        assert isinstance(success, list) and isinstance(failed, list), f"Некорректный формат ответа: {payload!r}"
        assert (task_id in success) or (task_id in failed), f"taskId отсутствует в success/failed: {payload!r}"