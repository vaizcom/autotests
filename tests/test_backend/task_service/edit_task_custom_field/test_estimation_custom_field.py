import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.task_service.conftest import _update_custom_field

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Estimation Custom Fields")
@allure.title("Edit Estimation Custom Field. Проверка успешного обновления значения и очистки поля.")
def test_edit_task_estimation_custom_field(owner_client, main_space, board_with_tasks, main_project):
    """
    Estimation Custom Fields. Проверка успешного обновления значения (ISO 8601 Duration) и очистки поля.
    """
    # Статические ID
    target_task_id = "696a1a04c7fd1dbba471efc2"
    estimation_field_id = "696e02ec2452157dfd7e2681"

    # Значения для теста
    # P1W2DT3H4M -> 1 Week, 2 Days, 3 Hours, 4 Minutes

    initial_value = "P1D"  # 1 Day (начальное значение)
    value_to_set = "P1W2DT3H4M"
    value_to_clear = ""  # Для очистки Estimation
    with allure.step(f"Pre-condition: Установка начального значения {initial_value}"):
        resp_pre = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_pre.status_code == 200

        # Устанавливаем начальное значение и проверяем ответ
        resp_initial = _update_custom_field(owner_client, main_space, target_task_id, estimation_field_id,
                                            initial_value)
        assert resp_initial.status_code == 200

        task_initial = resp_initial.json()["payload"]["task"]
        field_initial = next((cf for cf in task_initial.get("customFields", []) if cf.get("id") == estimation_field_id),
                             None)
        assert field_initial.get('value') == initial_value

    # 1. Перезапись значения (Overwrite)
    with allure.step(f"Action: Установка значения Estimation: {value_to_set}"):
        resp_set = _update_custom_field(owner_client, main_space, target_task_id, estimation_field_id, value_to_set)
        assert resp_set.status_code == 200, f"Ошибка при установке значения: {resp_set.text}"

        task = resp_set.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа (Estimation установлен)"):
            updated_field = next((cf for cf in task["customFields"] if cf["id"] == estimation_field_id), None)
            assert updated_field is not None
            assert updated_field["value"] == value_to_set, \
                f"Значение не обновилось. Ожидалось: '{value_to_set}', получено: '{updated_field['value']}'"

            assert_task_payload(task, board_with_tasks, main_project)

    with allure.step("Post-condition: Проверка сохранения данных в БД (через GET Task)"):
        resp_after_set = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after_set.status_code == 200

        task_db = resp_after_set.json().get("payload", {}).get("task")
        field_db = next((cf for cf in task_db.get("customFields", []) if cf.get("id") == estimation_field_id), None)

        assert field_db is not None
        assert field_db.get("value") == value_to_set, "Значение в БД не сохранилось"

    # 2. Очистка значения
    with allure.step("Action: Очистка поля Estimation (передача пустой строки ''."):
        resp_clear = _update_custom_field(owner_client, main_space, target_task_id, estimation_field_id, value_to_clear)
        assert resp_clear.status_code == 200, f"Ошибка при очистке: {resp_clear.text}"

        task_cleared = resp_clear.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа (поле очищено)"):
            cleared_field = next((cf for cf in task_cleared["customFields"] if cf["id"] == estimation_field_id), None)
            assert cleared_field is not None
            assert cleared_field.get("value") == "", \
                "Поле не очистилось. Ожидалось: "", получено: '{cleared_field.get('value')}'"

    with allure.step("Post-condition: Проверка очистки данных в БД (через GET Task)"):
        resp_after_clear = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after_clear.status_code == 200

        task_db_empty = resp_after_clear.json().get("payload", {}).get("task")
        field_db_empty = next(
            (cf for cf in task_db_empty.get("customFields", []) if cf.get("id") == estimation_field_id), None)

        assert field_db_empty is not None
        assert field_db_empty.get("value") == "", "Значение в БД не очистилось"


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Estimation Custom Fields")
@pytest.mark.parametrize("case_name, invalid_value, expected_message_part", [
    ("Random Text",
     "Random Text",
     'Expected ISO 8601 Duration format. Examples: "PT5H" (5 hours), "P3D" (3 days), "P2W" (2 weeks), "P2DT3H" (2 days 3 hours)'),

    ("Negative Duration",
     "-P1D",
     'Expected ISO 8601 Duration format. Examples: "PT5H" (5 hours), "P3D" (3 days), "P2W" (2 weeks), "P2DT3H" (2 days 3 hours)'),

    ("Invalid Format",
     "1W2D",
     'Expected ISO 8601 Duration format. Examples: "PT5H" (5 hours), "P3D" (3 days), "P2W" (2 weeks), "P2DT3H" (2 days 3 hours)'),  # Пропущена P
])
def test_edit_task_estimation_custom_field_negative(owner_client, main_space, case_name, invalid_value,
                                                    expected_message_part):
    allure.dynamic.title(f"Edit Estimation Custom Field. Negative: {case_name}")
    """
    Estimation Custom Fields. Negative tests.
    Проверяет валидацию формата ISO 8601 Duration.
    """
    target_task_id = "696a1a04c7fd1dbba471efc2"
    estimation_field_id = "696e02ec2452157dfd7e2681"

    with allure.step(f"Action: Отправка некорректного значения: {invalid_value}"):
        resp_edit = _update_custom_field(
            owner_client,
            main_space,
            target_task_id,
            estimation_field_id,
            invalid_value
        )

    with allure.step("Verification: Проверка ошибки валидации"):
        assert resp_edit.status_code == 400, \
            f"Ожидался статус 400, получен {resp_edit.status_code}. Тело: {resp_edit.text}"

        response_json = resp_edit.json()
        assert response_json["type"] == "EditTaskCustomField"

        error_data = response_json.get("error", {})
        assert error_data.get("code") == "InvalidForm"

        fields_errors = error_data.get("fields", [])
        assert len(fields_errors) > 0, "Список ошибок полей пуст"

        field_error = fields_errors[0]

        assert expected_message_part in field_error.get("meta", {}).get("message", "")