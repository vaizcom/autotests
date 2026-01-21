import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint, get_task_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Boolean Custom Fields")
@allure.title("Edit Boolean Custom Field. Positive Flows")
def test_edit_task_boolean_custom_field(owner_client, main_space, board_with_tasks, main_project):
    """
    Boolean Custom Fields. Проверка успешного переключения значения (True <-> False).
    """
    # Статические ID
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696e02dd2452157dfd7e2552"

    with allure.step("Pre-condition: Получение текущего состояния чекбокса"):
        resp_before = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_before.status_code == 200

        task_before = resp_before.json().get("payload", {}).get("task")
        cfs_before = task_before.get("customFields", [])
        cf_before = next((cf for cf in cfs_before if cf.get("id") == target_custom_field_id), None)
        assert cf_before is not None, f"Кастомное поле {target_custom_field_id} не найдено"

        # Определяем новое значение: инвертируем текущее
        # Если значение не установлено (None), считаем False -> ставим True
        current_val = cf_before.get("value")
        new_value = not current_val if isinstance(current_val, bool) else True

    with allure.step(f"Action: Установка значения Boolean = {new_value}"):
        resp_edit = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=new_value
        ))
        assert resp_edit.status_code == 200, f"Ошибка при редактировании: {resp_edit.text}"

        task = resp_edit.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа и обновленного поля"):
            updated_field = next((cf for cf in task["customFields"] if cf["id"] == target_custom_field_id), None)
            assert updated_field is not None

            assert updated_field["value"] is new_value, \
                f"Значение не обновилось. Ожидалось: {new_value}, получено: {updated_field['value']}"

            # Полная проверка структуры задачи
            assert_task_payload(task, board_with_tasks, main_project)

    with allure.step("Post-condition: Проверка сохранения в БД"):
        resp_after = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after.status_code == 200

        task_after = resp_after.json().get("payload", {}).get("task")
        updated_field = next(
            (cf for cf in task_after.get("customFields", []) if cf.get("id") == target_custom_field_id), None)

        assert updated_field is not None
        assert updated_field.get("value") is new_value


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Boolean Custom Fields")
@allure.title("Edit Boolean Custom Field. Negative: Invalid Type (String instead of Boolean)")
def test_edit_task_boolean_custom_field_invalid_type(owner_client, main_space):
    """
    Checkbox Custom Fields. Негативный тест: передача строки "true" вместо boolean true вызывает ошибку.
    """
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696e02dd2452157dfd7e2552"

    # Передаем строку, а не булево
    invalid_value = "true"

    with allure.step(f"Action: Отправка строки '{invalid_value}' вместо boolean"):
        resp_edit = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=invalid_value
        ))

    with allure.step("Verification: Проверка ошибки валидации"):
        response_json = resp_edit.json()
        assert response_json["payload"] is None
        assert response_json["type"] == "EditTaskCustomField"

        error_data = response_json.get("error", {})
        assert error_data.get("code") == "InvalidForm"

        fields_errors = error_data.get("fields", [])
        assert len(fields_errors) > 0

        field_error = fields_errors[0]
        # Проверяем имя поля (Boolean)
        assert field_error["name"] == "Boolean"
        assert "IllegalField" in field_error["codes"]

        meta = field_error.get("meta", {})
        assert meta.get("message") == "Expected boolean value (true or false)"
        assert meta.get("received") == invalid_value
