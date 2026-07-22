import os

import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from test_backend.task_service.utils import get_assignee

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Assignees edit Task")
@allure.title("Edit Task Assignees: Проверка редактирования только поля 'assignees'")
def test_edit_task_only_assignees(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное редактирование только поля 'assignees' задачи.
    """
    initial_task_data = make_task_in_main({"name": "Task with assignees", "assignees": []})
    task_id = initial_task_data.get("_id")
    initial_name = initial_task_data.get("name")
    initial_types = initial_task_data.get("types")

    new_assignees = get_assignee(owner_client, main_space)

    with allure.step(f"Отправляем запрос EditTask для редактирования только исполнителей задачи {task_id}"):
        edit_payload = {"assignees": new_assignees}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и обновленных исполнителей"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert set(task.get("assignees")) == set(new_assignees), \
            f"Исполнители не обновлены или не совпадают: {task.get('assignees')!r}"
        assert task.get("name") == initial_name, "Другие поля не должны были измениться"
        assert task.get("types") == initial_types, "Другие поля не должны были измениться"
        assert_task_payload(task, main_board, main_project)

@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Assignees edit Task")
@allure.title("Edit Task Assignees: Проверка удаления всех исполнителей в задаче передав пустой массив")
def test_edit_task_remove_all_assignees(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное удаление всех исполнителей из задачи передав пустой массив "assignees": [].
    """
    # Предполагаем, что get_assignee возвращает список из одного или нескольких исполнителей
    initial_assignees = get_assignee(owner_client, main_space)
    initial_task_data = make_task_in_main({"name": "Task with assignees to remove", "assignees": initial_assignees})
    task_id = initial_task_data.get("_id")
    initial_name = initial_task_data.get("name")
    initial_types = initial_task_data.get("types")

    with allure.step(f"Отправляем запрос EditTask для удаления всех исполнителей из задачи {task_id}"):
        edit_payload = {"assignees": []}
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и отсутствие исполнителей"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert task.get("assignees") == [], f"Исполнители не были удалены: {task.get('assignees')!r}"
        assert task.get("name") == initial_name, "Другие поля не должны были измениться"
        assert task.get("types") == initial_types, "Другие поля не должны были измениться"
        assert_task_payload(task, main_board, main_project)

@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Assignees edit Task")
@allure.title("Edit Task Assignees: Проверка изменения списка исполнителей задачи")
def test_edit_task_update_assignees(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет успешное изменение списка исполнителей задачи с одного набора на другой.
    """
    initial_assignee = get_assignee(owner_client, main_space)
    initial_task_data = make_task_in_main({"name": "Task with assignees to update", "assignees": initial_assignee})
    task_id = initial_task_data.get("_id")
    initial_name = initial_task_data.get("name")
    initial_types = initial_task_data.get("types")

    # Ищем нового исполнителя, который отличается от начального.
    new_assignee_id = get_assignee(owner_client, main_space)
    while new_assignee_id == initial_assignee:
        new_assignee_id = get_assignee(owner_client, main_space) # Обновляем переменную new_assignee_id
        if not new_assignee_id: # Защита от бесконечного цикла, если не удается получить новых исполнителей
            pytest.skip("Не удалось получить достаточное количество уникальных исполнителей для теста")

    updated_assignees_list = initial_assignee + new_assignee_id
    with allure.step(f"Отправляем запрос EditTask для изменения списка исполнителей задачи {task_id}"):
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, assignees=updated_assignees_list))

    with allure.step("Проверяем успешный статус и обновленный список исполнителей"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id
        assert set(task.get("assignees")) == set(updated_assignees_list), \
            f"Список исполнителей не обновлен или не совпадает: {task.get('assignees')!r}"
        assert task.get("name") == initial_name, "Другие поля не должны были измениться"
        assert task.get("types") == initial_types, "Другие поля не должны были измениться"
        assert_task_payload(task, main_board, main_project)


@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Assignees edit Task")
@allure.title("Edit Task Assignees: Проверка на уникалность ID исполнителей")
def test_edit_task_with_duplicate_assignees(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Проверяет, что при попытке добавить повторяющиеся ID исполнителей выводится ошибка.
    Корректность возвращаемого сообщения об ошибке
    """
    initial_task_data = make_task_in_main({"name": "Task for duplicate assignees", "assignees": []})
    task_id = initial_task_data.get("_id")

    assignee_id = get_assignee(owner_client, main_space)
    duplicate_assignees_list = assignee_id + assignee_id

    with allure.step(f"Отправляем запрос EditTask с повторяющимися ID исполнителей для задачи {task_id}"):
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, assignees=duplicate_assignees_list))

    with allure.step("Проверяем, что запрос завершился ошибкой 400 и содержит сообщение о дубликатах"):
        assert resp.status_code == 400, \
            f"Ожидался статус 400 для дублирующихся исполнителей, получен {resp.status_code}. Полный ответ: {resp.json()!r}"

        error_payload = resp.json().get("error")
        assert error_payload is not None, "В ответе об ошибке отсутствует 'error' секция."
        assert error_payload.get("fields")[0].get("codes") == ["Assignees array must not contain duplicate assignees"]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Assignees edit Task")
@allure.title("Edit Task Assignees: Назначение несуществующего member_id")
def test_edit_task_with_invalid_assignee_id(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Несуществующий member_id → 400 "One or more members are not part of this workspace".
    EditTask валидирует принадлежность пользователя к спейсу.
    В отличие от MultipleEditTasks, который этого НЕ делает (баг?).
    """
    initial_task_data = make_task_in_main({"name": "Task for invalid assignee", "assignees": []})
    task_id = initial_task_data.get("_id")

    invalid_member_id = "000000000000000000000000"

    with allure.step(f"Отправляем запрос EditTask с несуществующим member_id для задачи {task_id}"):
        resp = owner_client.post(**edit_task_endpoint(
            space_id=main_space, task_id=task_id, assignees=[invalid_member_id],
        ))

    with allure.step("Проверяем, что API отклонил запрос"):
        assert resp.status_code == 400, (
            f"Ожидался статус 400 для несуществующего member_id, получен {resp.status_code}. "
            f"Ответ: {resp.json()!r}"
        )


@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Assignees edit Task")
@allure.title("Edit Task Assignees: Назначение пользователя без доступа к борде (ожидаемо 200)")
def test_edit_task_assign_user_without_board_access(owner_client, main_space, make_task_in_main, main_board, main_project):
    """
    Пользователь есть в спейсе, но нет доступа к борде → API разрешает (200).
    Это ожидаемое поведение: API проверяет только принадлежность к спейсу,
    валидация доступа к борде была бы слишком тяжёлой для внутреннего API.
    UI ограничивает выбор — показывает только пользователей с доступом к борде.
    """
    project_client_email = os.getenv("PROJECT_CLIENT")
    assert project_client_email, "Не задана переменная окружения PROJECT_CLIENT"

    with allure.step("Находим member_id пользователя без доступа к борде"):
        resp = owner_client.post(**get_space_members_endpoint(space_id=main_space))
        assert resp.status_code == 200, resp.text
        members = resp.json()["payload"]["members"]
        target = next((m for m in members if m.get("email") == project_client_email), None)
        assert target, f"Пользователь {project_client_email} не найден в спейсе"
        no_board_member_id = target["_id"]

    with allure.step("Создаём задачу без assignees"):
        task = make_task_in_main({"name": "Task assign no board access", "assignees": []})
        task_id = task["_id"]

    with allure.step(f"Назначаем пользователя без доступа к борде ({project_client_email})"):
        resp = owner_client.post(**edit_task_endpoint(
            space_id=main_space, task_id=task_id, assignees=[no_board_member_id],
        ))

    with allure.step("API позволяет назначить пользователя без доступа к борде (200)"):
        assert resp.status_code == 200, (
            f"Ожидался 200 (API не валидирует доступ assignee к борде), "
            f"получен {resp.status_code}. Ответ: {resp.json()!r}"
        )
        task = resp.json()["payload"]["task"]
        assert no_board_member_id in task.get("assignees", []), (
            f"Пользователь без доступа к борде не добавлен в assignees: {task.get('assignees')}"
        )