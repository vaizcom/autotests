import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint
from test_backend.task_service.conftest import _update_custom_field

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Access Custom Fields")
@pytest.mark.parametrize(
    "client_fixture_name, expected_status_code",
    [
        ("owner_client", 200),
        ("manager_client", 200),
        ("member_client", 200),
        ("guest_client", 403),
    ],
)
def test_edit_task_estimation_custom_field_roles(
        request,
        main_space,
        owner_client,
        client_fixture_name,
        expected_status_code
):
    allure.dynamic.title(
        f"ESTIMATION {client_fixture_name} : Estimation Custom Fields. Проверка доступа к редактированию поля для роли {client_fixture_name}")

    """
    Estimation Custom Fields. Проверка доступа к редактированию поля Estimation для разных ролей.
    """
    client = request.getfixturevalue(client_fixture_name)
    target_task_id = "696a1a04c7fd1dbba471efc2"
    estimation_field_id = "696e02ec2452157dfd7e2681"
    new_value = "P2D"  # 2 days

    # Pre-condition: Очищаем поле через owner
    if expected_status_code == 200:
        _update_custom_field(owner_client, main_space, target_task_id, estimation_field_id, '')

    with allure.step(f"Action: Попытка изменения поля Estimation под ролью {client_fixture_name}"):
        resp_edit = client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=estimation_field_id,
            value=new_value
        ))

    with allure.step(f"Verification: Проверка статус-кода {expected_status_code}"):
        assert resp_edit.status_code == expected_status_code, \
            f"Неверный статус ответа для {client_fixture_name}. Ожидался {expected_status_code}, получен {resp_edit.status_code}"

    if expected_status_code == 200:
        with allure.step("Verification: Если доступ разрешен, проверяем, что значение действительно обновилось"):
            task = resp_edit.json().get("payload", {}).get("task", {})
            updated_field = next((cf for cf in task.get("customFields", []) if cf["id"] == estimation_field_id), None)

            assert updated_field is not None, "Кастомное поле не найдено в ответе"
            assert updated_field["value"] == new_value

    elif expected_status_code == 403:
        with allure.step("Verification: Проверка ошибки AccessDenied для guest"):
            response_json = resp_edit.json()
            assert response_json["payload"] is None
            assert response_json["type"] == "EditTaskCustomField"

            error = response_json.get("error", {})
            assert error.get("code") == "AccessDenied"