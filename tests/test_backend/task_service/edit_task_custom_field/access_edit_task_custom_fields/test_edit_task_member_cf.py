import allure
import pytest

from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint
from test_backend.task_service.utils import get_assignee

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
def test_edit_task_member_custom_field_roles(
        request,
        main_space,
        owner_client,
        client_fixture_name,
        expected_status_code
):
    """
    Member Custom Fields. Проверка доступа к редактированию поля Member для разных ролей.
    """
    allure.dynamic.title(f"MEMBER {client_fixture_name}: Edit Member Custom Field for Role: {client_fixture_name}")

    # Получаем клиента для теста (под кем будем делать запрос)
    client = request.getfixturevalue(client_fixture_name)

    # Статические данные для Member CF
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696e02e02452157dfd7e2577"

    # Подготавливаем валидное значение (список id участников).
    # Используем owner_client для получения данных, чтобы тест не падал на этапе подготовки данных у прав guest/foreign
    new_value = get_assignee(owner_client, main_space)

    with allure.step(f"Action: Попытка установить Member = {new_value} ролью {client_fixture_name}"):
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
        with allure.step("Verification: Значение обновилось"):
            task = resp_edit.json().get("payload", {}).get("task", {})
            updated_field = next((cf for cf in task.get("customFields", []) if cf["id"] == target_custom_field_id),
                                 None)
            assert updated_field is not None
            # Сравниваем списки
            assert sorted(updated_field["value"]) == sorted(new_value)

    elif expected_status_code == 403:
        with allure.step("Verification: Ошибка AccessDenied"):
            error = resp_edit.json().get("error", {})
            assert error.get("code") == "AccessDenied"
            assert error.get("meta", {}).get("kind") == "Board"