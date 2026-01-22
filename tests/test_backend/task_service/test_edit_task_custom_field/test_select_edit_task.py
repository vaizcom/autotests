import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint, get_task_endpoint

pytestmark = [pytest.mark.backend]


def _update_custom_field(client, space_id, task_id, field_id, value):
    """
    Вспомогательная функция для обновления значения кастомного поля.
    """
    return client.post(**edit_task_custom_field_endpoint(
        space_id=space_id,
        task_id=task_id,
        field_id=field_id,
        value=value
    ))


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Select Custom Fields")
@allure.title("Edit Select Custom Field. Positive Flows")
def test_edit_task_select_custom_field(owner_client, main_space, board_with_tasks, main_project):
    """
    Select Custom Fields. Проверка успешного выбора опций (установка массива ID опций) и очистки поля.
    """
    # Статические ID
    target_task_id = "696a1a04c7fd1dbba471efc2"
    select_field_id = "696e02e62452157dfd7e2608"

    # Значения для теста (ID опций селекта)
    value_to_set = ["764f797a466d5f6942715343", "6d7142524f49337a78456775"]
    value_to_clear = []

    with allure.step("Pre-condition: Проверка и очистка поля перед тестом"):
        resp_pre = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_pre.status_code == 200

        task_pre = resp_pre.json().get("payload", {}).get("task")
        field_pre = next((cf for cf in task_pre.get("customFields", []) if cf.get("id") == select_field_id), None)

        if field_pre and field_pre.get("value"):
            _update_custom_field(owner_client, main_space, target_task_id, select_field_id, value_to_clear)

    # 1. Установка значения
    with allure.step(f"Action: Выбор опций в поле Select: {value_to_set}"):
        resp_set = _update_custom_field(owner_client, main_space, target_task_id, select_field_id, value_to_set)
        assert resp_set.status_code == 200, f"Ошибка при установке значения: {resp_set.text}"

        task = resp_set.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа (опции выбраны)"):
            updated_field = next((cf for cf in task["customFields"] if cf["id"] == select_field_id), None)
            assert updated_field is not None
            # Сортируем для надежного сравнения списков
            assert sorted(updated_field["value"]) == sorted(value_to_set), \
                f"Значение не обновилось. Ожидалось: {value_to_set}, получено: {updated_field['value']}"

            assert_task_payload(task, board_with_tasks, main_project)

    # 2. Очистка значения
    with allure.step("Action: Очистка поля Select (передача пустого массива)"):
        resp_clear = _update_custom_field(owner_client, main_space, target_task_id, select_field_id, value_to_clear)
        assert resp_clear.status_code == 200, f"Ошибка при очистке: {resp_clear.text}"

        task_cleared = resp_clear.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа (поле очищено)"):
            cleared_field = next((cf for cf in task_cleared["customFields"] if cf["id"] == select_field_id), None)
            assert cleared_field is not None
            assert cleared_field["value"] == value_to_clear