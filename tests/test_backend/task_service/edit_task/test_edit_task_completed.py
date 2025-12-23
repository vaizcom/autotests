import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Completed edit Task")
@allure.title("Edit Task Completed: Проверка редактирования поля 'completed' с False на True")
def test_edit_task_completed(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное редактирование только поля 'completed' задачи с False на True.
    """
    initial_task_data = make_task_in_main({"name": "Task to complete", "completed": False})
    task_id = initial_task_data.get("_id")
    initial_name = initial_task_data.get("name")
    initial_due_start = initial_task_data.get("dueStart")

    new_completed_status = True

    with allure.step(f"Отправляем запрос EditTask для редактирования статуса завершения задачи {task_id}"):
        edit_payload = {"completed": new_completed_status}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и обновленный статус завершения"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert task.get("completed") == new_completed_status, \
            f"Статус завершения не обновлен: {task.get('completed')!r}"
        assert task.get("name") == initial_name, "Другие поля не должны были измениться"
        assert task.get("dueStart") == initial_due_start, "Другие поля не должны были измениться"
        assert task.get("completedAt") is not None, "Дата завершения должна быть установлена"
        assert_task_payload(task, main_board, main_project)

@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Completed edit Task")
@allure.title("Edit Task Completed: Проверка редактирования поля 'completed' с True на False")
def test_edit_task_uncompleted(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное редактирование только поля 'completed' задачи с True на False.
    """
    initial_task_data = make_task_in_main({"name": "Task to uncompleted", "completed": True})
    task_id = initial_task_data.get("_id")
    initial_name = initial_task_data.get("name")
    initial_due_start = initial_task_data.get("dueStart")

    new_completed_status = False

    with allure.step(f"Отправляем запрос EditTask для редактирования статуса завершения задачи {task_id} на False"):
        edit_payload = {"completed": new_completed_status}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и обновленный статус завершения"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert task.get("completed") == new_completed_status, \
            f"Статус завершения не обновлен: {task.get('completed')!r}"
        assert task.get("name") == initial_name, "Другие поля не должны были измениться"
        assert task.get("dueStart") == initial_due_start, "Другие поля не должны были измениться"
        assert task.get("completedAt") is None, "Дата завершения должна быть сброшена (None)"
        assert_task_payload(task, main_board, main_project)