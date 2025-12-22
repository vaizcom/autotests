import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.task_service.utils import get_random_type_id

pytestmark = [pytest.mark.backend]


@allure.title("Edit Task: Проверка редактирования поля 'types'")
def test_edit_task_types(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное редактирование поля 'types' задачи.
    """
    initial_type = get_random_type_id(owner_client, main_board, main_space)
    initial_task_data = make_task_in_main({"name": "Task with types", "types": [initial_type]})
    task_id = initial_task_data.get("_id")
    initial_name = initial_task_data.get("name")
    initial_assignees = initial_task_data.get("assignees")

    new_type = get_random_type_id(owner_client, main_board, main_space)
    while new_type == initial_type:
        new_type = get_random_type_id(owner_client, main_board, main_space)

    with allure.step(f"Отправляем запрос EditTask для редактирования только типов задачи {task_id}"):
        edit_payload = {"types": [new_type, initial_type]}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и обновленные типы"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert set(task.get("types")) == {new_type, initial_type}, \
            f"Типы задачи не обновлены или не совпадают: {task.get('types')!r}"
        assert task.get("name") == initial_name, "Другие поля не должны были измениться"
        assert task.get("assignees") == initial_assignees, "Другие поля не должны были измениться"
        assert_task_payload(task, main_board, main_project)


@allure.title("Edit Task: Проверка очистки поля 'types' пустым списком")
def test_edit_task_clear_types_with_empty_list(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешную очистку поля 'types' задачи путем передачи пустого списка.
    """
    initial_type = get_random_type_id(owner_client, main_board, main_space)
    initial_task_data = make_task_in_main({"name": "Task to clear types", "types": [initial_type]})
    task_id = initial_task_data.get("_id")

    with allure.step(f"Отправляем запрос EditTask для очистки типов задачи {task_id}"):
        edit_payload = {"types": []}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и очищенные типы"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert task.get("types") == [], \
            f"Типы задачи не были очищены. Получено: {task.get('types')!r}"
        assert_task_payload(task, main_board, main_project)


@pytest.mark.skip(reason="APP-4046")
@allure.title("Edit Task: Проверка ошибки при передаче повторяющихся типов (APP-4046)")
def test_edit_task_duplicate_types_error(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет, что при попытке редактирования задачи с повторяющимися типами
    возвращается ошибка и корректное сообщение.
    """
    initial_type = get_random_type_id(owner_client, main_board, main_space)
    initial_task_data = make_task_in_main({"name": "Task with types", "types": [initial_type]})
    task_id = initial_task_data.get("_id")

    with allure.step(f"Отправляем запрос EditTask с повторяющимися типами для задачи {task_id}"):
        edit_payload = {"types": [initial_type, initial_type]}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем, что запрос завершился ошибкой 400 и корректным сообщением"):
        assert resp.status_code == 400, f"Ожидался статус 400, получен {resp.status_code}"
        response_json = resp.json()

        # Проверяем наличие ключа 'error' и его содержимое
        assert "error" in response_json, "В ответе об ошибке отсутствует ключ 'error'"
        error_data = response_json["error"]

        # Проверяем общий код ошибки внутри 'error'
        assert error_data.get("code") == "InvalidForm", \
            f"Ожидался код ошибки 'InvalidForm' внутри 'error', получен '{error_data.get('code')}'"

        # Получаем первый объект ошибки поля
        error_field = error_data["fields"][0]
        assert error_field.get("name") == "types", \
            f"Ожидалась ошибка для поля 'types', получено для '{error_field.get('name')}'"
        assert "Types array must not contain duplicate types" in error_field.get("codes", []), \
            f"Неверное сообщение об ошибке для 'types'. Получено: {error_field.get('codes')!r}"