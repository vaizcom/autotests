import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_endpoint

pytestmark = [pytest.mark.backend]


def test_edit_task_minimal_payload(main_space, board_with_tasks, owner_client, main_project):
    """Проверяет минимальный вызов без опциональных полей."""

    task_id = "6939320d06e0921cfd8aeaab"

    resp = owner_client.post(**edit_task_endpoint(space_id=main_space, task_id=task_id))

    with allure.step("Проверяем успешный статус и содержимое ответа"):
        assert resp.status_code == 200
        task = resp.json()["payload"]["task"]
        assert task.get("_id") == task_id, f"Некорректный _id задачи: {task.get('_id')!r}, ожидался {task_id!r}"

        assert_task_payload(task, board_with_tasks, main_project)


@allure.title("Edit Task: проверка редактирования всех опциональных полей задачи")
def test_edit_task_endpoint_all_fields_provided(owner_client, main_space, make_task_in_main):
    """
    Проверяет успешное редактирование задачи, передав все возможные опциональные поля.
    Использует фикстуру make_task_in_main для создания задачи.
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
    new_assignees = ["6866313985fb8d104544ab6c"]  # Назначаем текущего пользователя
    new_completed_status = True
    new_name = "New Task Name Updated"  # Немного изменено для уникальности
    new_due_start = "2025-01-01T10:00:00.000Z"  # Добавлены миллисекунды для соответствия ISO
    new_due_end = "2025-01-01T12:00:00.000Z"
    new_priority = 2
    new_types = ["6866731185fb8d104544e82c"]
    new_cover_image = "6942c052a4dffd8a128af316"  # Немного изменено для уникальности

    with allure.step(f"Отправляем запрос EditTask для редактирования задачи {task_id} со всеми полями"):
        edit_payload = {
            "name": new_name,
            "completed": new_completed_status,
            "dueStart": new_due_start,  # Имя поля в camelCase
            "dueEnd": new_due_end,  # Имя поля в camelCase
            "priority": new_priority,
            "types": new_types,
            "assignees": new_assignees,
            "coverImage": new_cover_image,  # Имя поля в camelCase
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
        assert set(task.get("types")) == set(new_types), \
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