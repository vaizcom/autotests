import random
import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint, get_task_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Number Custom Fields")
@allure.title("Edit Number Custom Field. Positive Flows")
@pytest.mark.parametrize("number_type, base_value", [
    ("Positive Integer", 12345),
    ("Negative Integer", -9876),
    ("Float (Decimal)", 123.45),
    ("Negative Float", -55.99)
])
def test_edit_task_number_custom_field(owner_client, main_space, board_with_tasks, main_project, number_type,
                                       base_value):
    """
    Number Custom Fields. Проверка успешного обновления значения числового поля разными типами чисел (строкой).
    Проверяются: Положительные, Отрицательные, Дробные.
    """
    allure.dynamic.title(f"Edit Number Custom Field. Type: {number_type}")

    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696a1a10c7fd1dbba471f031"

    # 1. Получаем текущее значение
    with allure.step("Pre-condition: Проверка текущего значения"):
        resp_before = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_before.status_code == 200

        task_before = resp_before.json().get("payload", {}).get("task")
        cfs_before = task_before.get("customFields", [])
        cf_before = next((cf for cf in cfs_before if cf.get("id") == target_custom_field_id), None)

        current_val_str = str(cf_before.get("value")) if cf_before else None

    # 2. Формируем новое значение, гарантированно отличающееся от текущего
    # Добавляем случайное число, чтобы при повторных запусках значение менялось
    random_suffix = random.randint(1, 100)

    # Если это int (нет точки), просто прибавляем
    if isinstance(base_value, int):
        new_numeric_val = base_value + random_suffix
    else:
        # Если float, прибавляем немного к дробной части или целой
        new_numeric_val = round(base_value + (random_suffix * 0.1), 2)

    # Дополнительная защита: если вдруг все равно совпало с базой (маловероятно, но возможно)
    if str(new_numeric_val) == current_val_str:
        new_numeric_val += 1

    new_value_str = str(new_numeric_val)

    with allure.step(f"Action: Отправка запроса на изменение поля Number на '{new_value_str}'"):
        resp_edit = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=new_value_str
        ))
        assert resp_edit.status_code == 200, f"Ошибка при редактировании: {resp_edit.text}"

        task = resp_edit.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа и обновленного поля"):
            updated_field = next((cf for cf in task["customFields"] if cf["id"] == target_custom_field_id), None)
            assert updated_field is not None

            # Сравниваем строки
            assert str(updated_field["value"]) == new_value_str, \
                f"Значение поля не обновилось. Ожидалось: '{new_value_str}', получено: '{updated_field['value']}'"

            assert_task_payload(task, board_with_tasks, main_project)

    with allure.step(f"Post-condition: Проверка сохранения '{new_value_str}' в БД"):
        resp_after = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after.status_code == 200

        task_after = resp_after.json().get("payload", {}).get("task")
        cfs_after = task_after.get("customFields", [])
        updated_field = next((cf for cf in cfs_after if cf.get("id") == target_custom_field_id), None)

        assert updated_field is not None
        assert str(updated_field.get("value")) == new_value_str

@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Number Custom Fields")
@allure.title("Edit Number Custom Field. Negative: Integer value instead of string")
def test_edit_task_number_custom_field_with_int(owner_client, main_space):
    """
    Number Custom Fields. Проверка валидации: передача числа (int) вместо строки с числом вызывает ошибку InvalidForm.
    """
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696a1a10c7fd1dbba471f031"

    # ПЕРЕДАЕМ INT (123), А НЕ STR ("123")
    invalid_value = 123

    with allure.step(f"Action: Отправка запроса с типом Int ({invalid_value}) вместо String"):
        resp_edit = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=invalid_value
        ))

    with allure.step("Verification: Проверка ошибки валидации (InvalidForm)"):
        response_json = resp_edit.json()

        assert response_json["payload"] is None
        assert response_json["type"] == "EditTaskCustomField"

        error_data = response_json.get("error", {})
        assert error_data.get("code") == "InvalidForm"

        fields_errors = error_data.get("fields", [])
        assert len(fields_errors) > 0

        field_error = fields_errors[0]
        assert field_error["name"] == "Number"  # Или как оно называется в вашей системе
        assert "InvalidNumber" in field_error["codes"]

        meta = field_error.get("meta", {})
        # Теперь сообщение должно говорить, что ожидалась строка
        assert meta.get("message") == 'Expected numeric string (e.g., "123", "45.67")'
        assert meta.get("received") == invalid_value


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Number Custom Fields")
@pytest.mark.parametrize(
    "client_fixture_name, expected_status_code",
    [
        ("owner_client", 200),
        ("manager_client", 200),
        ("member_client", 200),
        ("guest_client", 403),
        ("foreign_client", 400),
    ],
)
def test_edit_task_number_custom_field_roles(
        request,
        main_space,
        client_fixture_name,
        expected_status_code
):
    """
    Number Custom Fields. Проверка доступа к редактированию числового поля для разных ролей.
    """
    allure.dynamic.title(f"Number Custom Fields. Проверка доступа (RBAC) для роли {client_fixture_name}")

    client = request.getfixturevalue(client_fixture_name)
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696a1a10c7fd1dbba471f031"

    # Генерируем СТРОКУ с числом
    new_value = str(random.randint(1, 500))

    with allure.step(f"Action: Попытка изменения поля Number ролью {client_fixture_name}"):
        resp_edit = client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=new_value
        ))

    with allure.step(f"Verification: Проверка статус-кода {expected_status_code}"):
        assert resp_edit.status_code == expected_status_code, \
            f"Неверный статус для {client_fixture_name}. Ожидался {expected_status_code}, получен {resp_edit.status_code}"

    if expected_status_code == 200:
        with allure.step("Verification: Проверка обновления значения"):
            task = resp_edit.json().get("payload", {}).get("task", {})
            updated_field = next((cf for cf in task.get("customFields", []) if cf["id"] == target_custom_field_id),
                                 None)
            assert updated_field is not None
            # Сравниваем как строки
            assert str(updated_field["value"]) == new_value

    elif expected_status_code == 403:
        with allure.step("Verification: Проверка тела ошибки AccessDenied"):
            error = resp_edit.json().get("error", {})
            assert error.get("code") == "AccessDenied"
            assert error.get("meta", {}).get("kind") == "Board"

    elif expected_status_code == 400:
        with allure.step("Verification: Проверка тела ошибки SpaceIdNotSpecified"):
            error = resp_edit.json().get("error", {})
            assert error.get("code") == "SpaceIdNotSpecified"