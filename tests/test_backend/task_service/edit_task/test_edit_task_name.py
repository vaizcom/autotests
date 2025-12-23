import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Name edit Task")
@allure.title("Edit Task Name: Проверка редактирования поля 'name'")
def test_edit_task_name(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное редактирование  поля 'name' задачи.
    """
    initial_task_data = make_task_in_main({"name": "Initial Task Name"})
    task_id = initial_task_data.get("_id")
    initial_due_start = initial_task_data.get("dueStart")
    initial_priority = initial_task_data.get("priority")
    initial_completed = initial_task_data.get("completed")

    new_name = "Updated Task Name"

    with allure.step(f"Отправляем запрос EditTask для редактирования только имени задачи {task_id}"):
        edit_payload = {"name": new_name}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и обновленное имя"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert task.get("name") == new_name, f"Имя задачи не обновлено: {task.get('name')!r}"
        assert task.get("dueStart") == initial_due_start, "Другие поля не должны были измениться"
        assert task.get("priority") == initial_priority, "Другие поля не должны были измениться"
        assert task.get("completed") == initial_completed, "Другие поля не должны были измениться"
        assert_task_payload(task, main_board, main_project)