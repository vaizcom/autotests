import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import (
    edit_task_custom_field_endpoint,
    duplicate_task_endpoint,
)
from test_backend.data.endpoints.History.history_utils import (
    assert_get_history_event,
    assert_get_history_no_event,
)

pytestmark = [pytest.mark.backend]


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[General] создание задачи без CF не генерирует CUSTOM_FIELD_CHANGED")
def test_task_create_no_cf_changed_events(main_client, space_for_history, temp_task, text_custom_field):
    """
    Проверяем что создание задачи без заполнения кастомных полей
    не генерирует событий CUSTOM_FIELD_CHANGED.
    CF-поле существует на борде, но значение не задано.
    """
    space_id = space_for_history["space_id"]
    task_id = temp_task
    field_id = text_custom_field["field_id"]

    with allure.step("Проверяем что для новой задачи нет событий CUSTOM_FIELD_CHANGED"):
        assert_get_history_no_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
        )


@allure.parent_suite("History Service")
@allure.suite("Task History")
@allure.sub_suite("CUSTOM_FIELD_CHANGED events (APP-3813)")
@allure.title("[General] дублирование задачи с CF не дублирует CUSTOM_FIELD_CHANGED")
def test_duplicate_task_no_cf_changed_events(main_client, space_for_history, board_for_history, temp_task, text_custom_field):
    """
    Проверяем что при дублировании задачи с заполненным кастомным полем
    в истории дубля НЕ появляется CUSTOM_FIELD_CHANGED.
    Значения CF копируются, но это не отдельное действие пользователя.
    """
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    task_id = temp_task
    field_id = text_custom_field["field_id"]

    with allure.step("Устанавливаем значение Text CF на оригинальной задаче"):
        resp = main_client.post(**edit_task_custom_field_endpoint(
            space_id=space_id, task_id=task_id, field_id=field_id, value="original value",
        ))
        assert resp.status_code == 200, f"Ошибка при установке CF: {resp.text}"

    with allure.step("Ожидаем CUSTOM_FIELD_CHANGED на оригинальной задаче"):
        assert_get_history_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
            expected_data={"_id": task_id, "fieldId": field_id, "isCleared": False},
        )

    with allure.step("Дублируем задачу"):
        resp = main_client.post(**duplicate_task_endpoint(
            space_id=space_id, task_id=task_id, board_id=board_id,
        ))
        assert resp.status_code == 200, f"Ошибка при дублировании: {resp.text}"
        dup_task_id = resp.json()["payload"]["task"]["_id"]

    with allure.step("Проверяем что у дубля нет CUSTOM_FIELD_CHANGED событий"):
        assert_get_history_no_event(
            client=main_client,
            space_id=space_id,
            kind="Task",
            kind_id=dup_task_id,
            expected_event_key="CUSTOM_FIELD_CHANGED",
        )
