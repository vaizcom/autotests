from datetime import timedelta, datetime

import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.task_service.utils import get_current_timestamp, get_due_end

pytestmark = [pytest.mark.backend]


@allure.title("Edit Task: Проверка редактирования поля 'dueStart'")
def test_edit_task_due_start(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное редактирование поля 'dueStart' задачи.
    """
    initial_task_data = make_task_in_main({"name": "Task with due start", "due_start": get_current_timestamp()})
    task_id = initial_task_data.get("_id")
    initial_name = initial_task_data.get("name")
    initial_due_end = initial_task_data.get("dueEnd")

    new_due_start = (datetime.fromisoformat(get_current_timestamp()) + timedelta(weeks=1)).isoformat(timespec='seconds')

    with allure.step("Отправляем запрос EditTask для редактирования даты начала, увеличив на неделю от ранее установленной даты"):
        edit_payload = {"dueStart": new_due_start}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и обновленную дату начала"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert task.get("dueStart").startswith(new_due_start[:19]), \
            f"Дата начала не обновлена: {task.get('dueStart')!r}"
        assert task.get("name") == initial_name, "Другие поля не должны были измениться"
        assert task.get("dueEnd") == initial_due_end, "Другие поля не должны были измениться"
        assert_task_payload(task, main_board, main_project)


@allure.title("Edit Task: Проверка редактирования поля 'dueEnd'")
def test_edit_task_due_end(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное редактирование  поля 'dueEnd' задачи.
    """
    due_start = get_current_timestamp()
    due_end = (datetime.fromisoformat(get_current_timestamp()) + timedelta(days=1)).isoformat(timespec='seconds')
    initial_task_data = make_task_in_main({"name": "Task with due end", "due_start":due_start, "due_end":due_end})
    task_id = initial_task_data.get("_id")
    initial_name = initial_task_data.get("name")
    initial_due_start = initial_task_data.get("dueStart")

    new_due_end = get_due_end()

    with allure.step(f"Отправляем запрос EditTask для редактирования даты окончания {task_id}"):
        edit_payload = {"dueEnd": new_due_end}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и обновленную дату окончания"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert task.get("dueEnd").startswith(new_due_end[:19]), \
            f"Дата окончания не обновлена: {task.get('dueEnd')!r}"
        assert task.get("name") == initial_name, "Другие поля не должны были измениться"
        assert task.get("dueStart") == initial_due_start, "Другие поля не должны были измениться"
        assert_task_payload(task, main_board, main_project)


@allure.title("Edit Task: Проверка ошибки, когда дата начала позже даты окончания")
def test_edit_task_due_start_after_due_end_error(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет, что при попытке установить dueStart позже, чем dueEnd,
    возвращается ошибка валидации.
    """
    due_start = get_current_timestamp()
    due_end = get_due_end()
    initial_task_data = make_task_in_main({"name": "Task with due end", "due_start": due_start, "due_end": due_end})
    task_id = initial_task_data.get("_id")

    with allure.step("Отправляем запрос EditTask с dueStart позже dueEnd"):
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, dueStart= due_end, dueEnd= due_start))

    with allure.step("Проверяем статус ошибки и содержимое тела ответа"):
        assert resp.status_code == 400, f"Ожидался статус 400 (Bad Request), получен {resp.status_code}"
        error_payload = resp.json()
        assert error_payload.get("error", {}).get("code") == "InvalidForm"
        assert any(
            field.get("name") == "dueStart" and "Start date cannot be after end date" in field.get("codes", [])
            for field in error_payload.get("error", {}).get("fields", [])
        ), "Ожидалось сообщение об ошибке 'Start date cannot be after end date' для поля 'dueStart'"