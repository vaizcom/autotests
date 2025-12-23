import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.task_service.utils import get_assignee, get_current_timestamp, get_due_end, get_priority, \
    get_random_type_id

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Access edit Task")
@pytest.mark.parametrize(
    "client_fixture_name, expected_status_code",
    [
        ("owner_client", 200),
        ("manager_client", 200),
        ("member_client", 200),
        ("guest_client", 403),
    ],
)
def test_edit_task_minimal_payload(
    request, main_space, main_board, owner_client, main_project, make_task_in_main,
    client_fixture_name, expected_status_code
):
    allure.dynamic.title(f"Edit Task: Проверка минимального редактирования задачи без опциональных полей для роли {client_fixture_name}")
    """
    Проверяет минимальный вызов эндпоинта редактирования задачи,
    убеждаясь, что редактирование без опциональных полей проходит успешно
    и базовая информация о задаче остается корректной.
    """
    client = request.getfixturevalue(client_fixture_name)

    with allure.step("Создаем новую задачу с минимальными данными"):
        initial_task_data = make_task_in_main({
            "name": "Edit Task: Задача для редактирования",
        })
    task_id = initial_task_data.get("_id")

    with allure.step(f"Пользователь с ролью {client_fixture_name} отправляет запрос на редактирование задачи {task_id} без дополнительных полей"):
        resp = client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id))

    with allure.step(f"Проверяем ожидаемый статус код {expected_status_code}"):
        assert resp.status_code == expected_status_code, \
            f"Неверный статус код для {client_fixture_name}: ожидался {expected_status_code}, получен {resp.status_code}"

    if expected_status_code == 200:
        with allure.step("Проверяем успешный статус и содержимое ответа"):
            task = resp.json()["payload"]["task"]
            assert task.get("_id") == task_id, f"Некорректный _id задачи: {task.get('_id')!r}, ожидался {task_id!r}"
            # Имя задачи должно остаться первоначальным, так как не было передано в payload
            assert task.get("name") == "Edit Task: Задача для редактирования"
            assert_task_payload(task, main_board, main_project)
    else:
        with allure.step("Проверяем сообщение об ошибке для запрещенного доступа"):
            error_message = resp.json()
            assert error_message.get("error", {}).get("code") == "AccessDenied"


@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Access edit Task")
@pytest.mark.parametrize(
    "client_fixture_name, expected_status_code",
    [
        ("owner_client", 200),
        ("manager_client", 200),
        ("member_client", 200),
        ("guest_client", 403),
    ],
)
def test_edit_task_endpoint_all_fields(
    request, owner_client, main_space, make_task_in_main, main_board, main_project,
    client_fixture_name, expected_status_code
):
    allure.dynamic.title(f"Edit Task: проверка редактирования всех опциональных полей задачи для роли {client_fixture_name}")

    """
    Проверяет успешное редактирование задачи, передав все возможные опциональные поля.
    """
    client_to_test = request.getfixturevalue(client_fixture_name)

    initial_task_name = f"Edit Task: Задача для редактирования от {client_fixture_name}"
    initial_task_data = make_task_in_main({
        "name": initial_task_name,
    })
    task_id = initial_task_data.get("_id")

    with allure.step("Проверяем начальное состояние задачи до редактирования"):
        assert initial_task_data.get("types") == [], \
            f"Начальное 'types' должно быть пустым, получено: {initial_task_data.get('types')!r}"
        assert initial_task_data.get("assignees") == [], \
            f"Начальное 'assignees' должно быть пустым, получено: {initial_task_data.get('assignees')!r}"
        assert initial_task_data.get("dueStart") is None, \
            f"Начальное 'dueStart' должно быть NULL, получено: {initial_task_data.get('dueStart')!r}"
        assert initial_task_data.get("dueEnd") is None, \
            f"Начальное 'dueEnd' должно быть NULL, получено: {initial_task_data.get('dueEnd')!r}"
        assert initial_task_data.get("completedAt") is None, \
            f"Начальное 'completedAt' должно быть NULL, получено: {initial_task_data.get('completedAt')!r}"
        assert initial_task_data.get("completed") is False, \
            f"Начальное 'completed' должно быть false, получено: {initial_task_data.get('completed')!r}"
        assert initial_task_data.get("priority") == 1, \
            f"Начальный 'priority' должен быть 1, получен: {initial_task_data.get('priority')!r}"
        assert initial_task_data.get("name") == initial_task_name, \
            f"Начальное 'name' не соответствует ожидаемому: {initial_task_data.get('name')!r}"

    # Данные для обновления, включая новые поля
    new_assignees = get_assignee(owner_client, main_space)
    new_completed_status = True
    new_name = f"New Task Name Updated by {client_fixture_name}"
    new_due_start = get_current_timestamp()
    new_due_end = get_due_end()
    new_priority = get_priority()
    new_types = get_random_type_id(owner_client, main_board, main_space)
    new_cover_image = "69440700136ecd5583dae514"

    with allure.step(f"Пользователь с ролью {client_fixture_name} отправляет запрос EditTask для редактирования задачи со всеми полями"):
        edit_payload = {
            "name": new_name,
            "completed": new_completed_status,
            "dueStart": new_due_start,
            "dueEnd": new_due_end,
            "priority": new_priority,
            "types": [new_types],
            "assignees": new_assignees,
            "coverImage": new_cover_image,
        }
        resp = client_to_test.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step(f"Проверяем ожидаемый статус код {expected_status_code}"):
        assert resp.status_code == expected_status_code, \
            f"Неверный статус код для {client_fixture_name}: ожидался {expected_status_code}, получен {resp.status_code}"

    if expected_status_code == 200:
        with allure.step("Проверяем успешный статус и структуру ответа с обновленными данными"):
            body = resp.json()
            assert body.get("type") == "EditTask", f"Некорректный type: {body.get('type')!r}"
            payload = body.get("payload")
            assert payload is not None, "Payload отсутствует в ответе"

            task = payload.get("task")
            assert task is not None, "Task отсутствует в payload"

            # Проверяем ID
            assert task.get("_id") == task_id, f"ID задачи в ответе не совпадает: {task.get('_id')!r}"

            # Проверяем обновленные поля
            assert task.get("name") == new_name, f"Имя задачи не обновлено: {task.get('name')!r}"
            assert task.get("completed") == new_completed_status, \
                f"Статус завершения не обновлен: {task.get('completed')!r}"
            assert task.get("priority") == new_priority, f"Приоритет задачи не обновлен: {task.get('priority')!r}"

            # Для списков (assignees, types) важно проверить содержимое, а не порядок
            assert set(task.get("assignees")) == set(new_assignees), \
                f"Исполнители не обновлены или не совпадают: {task.get('assignees')!r}"
            assert set(task.get("types")) == set([new_types]), \
                f"Типы задачи не обновлены или не совпадают: {task.get('types')!r}"

            # Для дат - API может возвращать их в слегка отличающемся формате (например, с миллисекундами)
            # Поэтому лучше проверить, что строка даты содержит ожидаемые значения.
            assert task.get("dueStart").startswith(new_due_start[:19]), \
                f"Дата начала не обновлена: {task.get('dueStart')!r}"
            assert task.get("dueEnd").startswith(new_due_end[:19]), \
                f"Дата окончания не обновлена: {task.get('dueEnd')!r}"

            assert task.get("coverAR") is not None
            assert task.get("coverColor") is not None
            assert task.get("coverUrl") is not None
    else:
        with allure.step("Проверяем сообщение об ошибке для запрещенного доступа"):
            error_message = resp.json()
            assert error_message.get("error", {}).get("code") == "AccessDenied"