import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint
from test_backend.task_service.utils import get_assignee, get_current_timestamp, get_due_end, get_priority, \
    get_random_type_id

pytestmark = [pytest.mark.backend]


@allure.title("Edit Task: Проверка минимального редактирования задачи без опциональных полей")
def test_edit_task_minimal_payload(main_space, main_board, owner_client, main_project, make_task_in_main):
    """
    Проверяет минимальный вызов эндпоинта редактирования задачи,
    убеждаясь, что редактирование без опциональных полей проходит успешно
    и базовая информация о задаче остается корректной.
    """
    with allure.step("Создаем новую задачу с минимальными данными"):
        initial_task_data = make_task_in_main({
            "name": "Edit Task: Задача для редактирования",
        })
    task_id = initial_task_data.get("_id")

    with allure.step(f"Отправляем запрос на редактирование задачи {task_id} без дополнительных полей"):
        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id))

    with allure.step("Проверяем успешный статус и содержимое ответа"):
        assert resp.status_code == 200
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id, f"Некорректный _id задачи: {task.get('_id')!r}, ожидался {task_id!r}"
        assert_task_payload(task, main_board, main_project)


@allure.title("Edit Task: проверка редактирования всех опциональных полей задачи")
def test_edit_task_endpoint_all_fields(owner_client, main_space, make_task_in_main, main_board):
    """
    Проверяет успешное редактирование задачи, передав все возможные опциональные поля.
    """
    initial_task_data = make_task_in_main({
        "name": "Edit Task: Задача для редактирования",
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
        assert initial_task_data.get("name") == "Edit Task: Задача для редактирования", \
            f"Начальное 'name' не соответствует ожидаемому: {initial_task_data.get('name')!r}"

    # Данные для обновления, включая новые поля
    new_assignees = get_assignee(owner_client, main_space)  # случайный member_id
    new_completed_status = True
    new_name = "New Task Name Updated"
    new_due_start = get_current_timestamp()
    new_due_end = get_due_end()
    new_priority = get_priority()
    new_types = get_random_type_id(owner_client, main_board, main_space)
    new_cover_image = "69440700136ecd5583dae514"  # coverImage должен быть в базе

    with allure.step("Отправляем запрос EditTask для редактирования задачи со всеми полями"):
        edit_payload = {
            "name": new_name,
            "completed": new_completed_status,
            "dueStart": new_due_start,
            "dueEnd": new_due_end,
            "priority": new_priority,
            "types": [new_types],
            "assignees": new_assignees,
            "coverImage": new_cover_image,
            # Добавьте другие поля для редактирования здесь, если необходимо
        }

        resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id, **edit_payload))

    with allure.step("Проверяем успешный статус и структуру ответа с обновленными данными"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"
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
            f"Дата начала не обновлена: {task.get('dueStart')!r}"  # Сравниваем до секунд
        assert task.get("dueEnd").startswith(new_due_end[:19]), \
            f"Дата окончания не обновлена: {task.get('dueEnd')!r}"  # Сравниваем до секунд

        assert task.get("coverAR") is not None
        assert task.get("coverColor") is not None
        assert task.get("coverUrl") is not None