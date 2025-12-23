import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.task_service.utils import get_priority

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Priority edit Task")
@allure.title("Edit Task: Проверка редактирования поля 'priority'")
def test_edit_task_priority(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное редактирование только поля 'priority' задачи.
    """
    initial_task_data = make_task_in_main({"name": "Task with priority", "priority": 1})
    task_id = initial_task_data.get("_id")
    initial_name = initial_task_data.get("name")
    initial_completed = initial_task_data.get("completed")

    new_priority = get_priority()  # Получаем случайный приоритет

    with allure.step(f"Отправляем запрос EditTask для редактирования только приоритета задачи {task_id}"):
        edit_payload = {"priority": new_priority}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и обновленный приоритет"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert task.get("priority") == new_priority, \
            f"Приоритет задачи не обновлен: {task.get('priority')!r}"
        assert task.get("name") == initial_name, "Другие поля не должны были измениться"
        assert task.get("completed") == initial_completed, "Другие поля не должны были измениться"
        assert_task_payload(task, main_board, main_project)

@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Priority edit Task")
@allure.title("Edit Task Priority: Проверка передачи невалидного значения в поле 'priority'")
def test_edit_task_invalid_priority_value(owner_client, main_space, make_task_in_main):
    """
    Проверяет, что система возвращает ошибку при попытке передать невалидное значение в поле 'priority'.
    """
    initial_task_data = make_task_in_main({"name": "Task with invalid priority check", "priority": 1})
    task_id = initial_task_data.get("_id")
    invalid_priority = 10  # Невалидное значение для приоритета

    with allure.step(f"Отправляем запрос EditTask с невалидным приоритетом - {invalid_priority}"):
        edit_payload = {"priority": invalid_priority}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем, что запрос завершился с ошибкой и соответствующим кодом"):
        assert resp.status_code == 400, f"Ожидался статус 400, получен {resp.status_code}"
        error_payload = resp.json()
        assert error_payload.get("type") == "EditTask"
        assert error_payload.get("error").get("code") == "InvalidForm"
        assert "InvalidEnum" in error_payload.get("error").get("fields")[0].get("codes")
        assert error_payload.get("error").get("originalType") == "EditTask"