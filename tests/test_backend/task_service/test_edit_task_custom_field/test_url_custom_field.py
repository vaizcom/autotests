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
@allure.sub_suite("URL Custom Fields")
@allure.title("Edit URL Custom Field. Проверка успешного обновления значения и очистки поля.")
def test_edit_task_url_custom_field(owner_client, main_space, board_with_tasks, main_project):
    """
    URL Custom Fields. Проверка успешного обновления значения (valid URL) и очистки поля.
    """
    # Статические ID
    target_task_id = "696a1a04c7fd1dbba471efc2"
    url_field_id = "696e02e92452157dfd7e2631"

    # Значения для теста
    value_to_set = "https://www.google.com"
    value_to_clear = ""

    with allure.step("Pre-condition: Проверка и очистка поля перед тестом"):
        resp_pre = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_pre.status_code == 200

        task_pre = resp_pre.json().get("payload", {}).get("task")
        field_pre = next((cf for cf in task_pre.get("customFields", []) if cf.get("id") == url_field_id), None)

        if field_pre and field_pre.get("value"):
            _update_custom_field(owner_client, main_space, target_task_id, url_field_id, value_to_clear)

    # 1. Установка значения
    with allure.step(f"Action: Установка значения URL: {value_to_set}"):
        resp_set = _update_custom_field(owner_client, main_space, target_task_id, url_field_id, value_to_set)
        assert resp_set.status_code == 200, f"Ошибка при установке значения: {resp_set.text}"

        task = resp_set.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа (URL установлен)"):
            updated_field = next((cf for cf in task["customFields"] if cf["id"] == url_field_id), None)
            assert updated_field is not None
            assert updated_field["value"] == value_to_set, \
                f"Значение не обновилось. Ожидалось: '{value_to_set}', получено: '{updated_field['value']}'"

            assert_task_payload(task, board_with_tasks, main_project)

    with allure.step("Post-condition: Проверка сохранения данных в БД (через GET Task)"):
        resp_after_set = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after_set.status_code == 200

        task_db = resp_after_set.json().get("payload", {}).get("task")
        field_db = next((cf for cf in task_db.get("customFields", []) if cf.get("id") == url_field_id), None)

        assert field_db is not None
        assert field_db.get("value") == value_to_set, "Значение в БД не сохранилось"

    # 2. Очистка значения
    with allure.step("Action: Очистка поля URL (передача пустой строки)"):
        resp_clear = _update_custom_field(owner_client, main_space, target_task_id, url_field_id, value_to_clear)
        assert resp_clear.status_code == 200, f"Ошибка при очистке: {resp_clear.text}"

        task_cleared = resp_clear.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа (поле очищено)"):
            cleared_field = next((cf for cf in task_cleared["customFields"] if cf["id"] == url_field_id), None)
            assert cleared_field is not None
            assert cleared_field["value"] == value_to_clear, \
                f"Поле не очистилось. Ожидалось: '', получено: '{cleared_field['value']}'"

    with allure.step("Post-condition: Проверка очистки данных в БД (через GET Task)"):
        resp_after_clear = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after_clear.status_code == 200

        task_db_empty = resp_after_clear.json().get("payload", {}).get("task")
        field_db_empty = next(
            (cf for cf in task_db_empty.get("customFields", []) if cf.get("id") == url_field_id), None)

        assert field_db_empty is not None
        assert field_db_empty.get("value") == value_to_clear, "Значение в БД не очистилось"


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("URL Custom Fields")
@pytest.mark.parametrize("case_name, invalid_value, expected_field_code, expected_message", [
    ("No Protocol",
     "google.com",
     "InvalidURL",
     'Expected valid URL (e.g., "https://example.com")'),

    ("Just Text",
     "some_random_text",
     "InvalidURL",
     'Expected valid URL (e.g., "https://example.com")')
            ])
def test_edit_task_url_custom_field_negative(owner_client, main_space, case_name, invalid_value, expected_field_code, expected_message):
    allure.dynamic.title(f"Edit URL Custom Field. Negative: {case_name}")
    """
    URL Custom Fields. Negative tests.
    Проверяет валидацию формата URL (наличие протокола http/https).
    """
    target_task_id = "696a1a04c7fd1dbba471efc2"
    url_field_id = "696e02e92452157dfd7e2631"

    with allure.step(f"Action: Отправка некорректного значения: {invalid_value}"):
        resp_edit = _update_custom_field(
            owner_client,
            main_space,
            target_task_id,
            url_field_id,
            invalid_value
        )

    with allure.step("Verification: Проверка ошибки валидации"):
        # Ожидаем 400 Bad Request
        assert resp_edit.status_code == 400, \
            f"Ожидался статус 400, получен {resp_edit.status_code}. Тело: {resp_edit.text}"

        response_json = resp_edit.json()
        assert response_json["type"] == "EditTaskCustomField"

        error_data = response_json.get("error", {})
        # Основной код ошибки формы
        assert error_data.get("code") == "InvalidForm", \
            f"Ожидался код ошибки InvalidForm, получен {error_data.get('code')}"

        # Детализация ошибки по конкретному полю
        fields_errors = error_data.get("fields", [])
        assert len(fields_errors) > 0, "Список ошибок полей пуст"

        field_error = fields_errors[0]

        # Проверка наличия ожидаемого кода ошибки (InvalidURL) в списке кодов поля
        error_codes = field_error.get("codes", [])
        assert expected_field_code in error_codes, \
            f"Код {expected_field_code} не найден в ошибке поля. Получено: {error_codes}"
        meta = field_error.get("meta", {})
        assert meta.get("message") == expected_message, \
            f"Некорректное сообщение об ошибке. Ожидалось: '{expected_message}', получено: '{meta.get('message')}'"