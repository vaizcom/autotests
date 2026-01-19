import uuid

import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Text Custom Fields")
@allure.title("Edit Text Custom Field. RBAC")
@pytest.mark.parametrize(
    "client_fixture_name, expected_status_code",
    [
        ("owner_client", 200),
        ("manager_client", 200),
        ("member_client", 200),
        ("guest_client", 403),
    ],
)
def test_edit_task_text_custom_field_roles(
        request,
        main_space,
        client_fixture_name,
        expected_status_code
):
    """
    Text Custom Fields. Проверка доступа к редактированию текстового поля для разных ролей.
    """
    client = request.getfixturevalue(client_fixture_name)
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696a1a0ac7fd1dbba471f014"
    new_value = f"RoleTest-{uuid.uuid4().hex[:6]}"

    with allure.step(f"Action: Попытка изменения поля Text под ролью {client_fixture_name}"):
        resp_edit = client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=new_value
        ))

    with allure.step(f"Verification: Проверка статус-кода {expected_status_code}"):
        assert resp_edit.status_code == expected_status_code, \
            f"Неверный статус ответа для {client_fixture_name}. Ожидался {expected_status_code}, получен {resp_edit.status_code}"

    if expected_status_code == 200:
        with allure.step("Verification: Если доступ разрешен, проверяем, что значение действительно обновилось"):
            task = resp_edit.json().get("payload", {}).get("task", {})
            updated_field = next((cf for cf in task.get("customFields", []) if cf["id"] == target_custom_field_id),
                                 None)

            assert updated_field is not None, "Кастомное поле не найдено в ответе"
            assert updated_field["value"] == new_value