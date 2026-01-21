import allure
import pytest

from tests.test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from tests.test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint, get_task_endpoint
from tests.test_backend.task_service.utils import get_assignee

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Member Custom Fields")
@allure.title("Edit Member Custom Field. Positive Flows")
@pytest.mark.parametrize("iterations", [1, 3], ids=["single_member", "multiple_members"])
def test_edit_task_member_custom_field(owner_client, main_space, board_with_tasks, main_project, iterations):
    """
    Member Custom Fields. Проверка успешного назначения.
    Параметризация:
    - single_member: вызываем get_assignee 1 раз (обычный кейс).
    - multiple_members: вызываем get_assignee несколько раз и объединяем результаты, чтобы получить массив из нескольких участников.
    """
    # Статические ID
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696e02e02452157dfd7e2577"

    with allure.step(f"Pre-condition: Формирование списка участников (вызовов get_assignee: {iterations})"):
        members_set = set()
        for _ in range(iterations):
            # get_assignee возвращает список ID. Добавляем их в множество для уникальности.
            current_ids = get_assignee(owner_client, main_space)
            members_set.update(current_ids)

        new_value = list(members_set)
        assert new_value, "Список участников пуст"

    with allure.step(f"Action: Установка значения Member = {new_value}"):
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
            assert updated_field is not None, "Поле не найдено в ответе"

            # Сортируем списки для сравнения
            assert sorted(updated_field["value"]) == sorted(new_value), \
                f"Значение не обновилось. Ожидалось: {new_value}, получено: {updated_field['value']}"

            assert_task_payload(task, board_with_tasks, main_project)

    with allure.step("Post-condition: Проверка сохранения в БД"):
        resp_after = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after.status_code == 200

        task_after = resp_after.json().get("payload", {}).get("task")
        updated_field = next(
            (cf for cf in task_after.get("customFields", []) if cf.get("id") == target_custom_field_id), None)

        assert updated_field is not None
        assert sorted(updated_field.get("value")) == sorted(new_value)


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Member Custom Fields")
@allure.title("Edit Member Custom Field. Negative Scenarios")
@pytest.mark.parametrize("case_key, expected_code, expected_message", [
    (
            "duplicates",
            "IllegalField",
            "Duplicate member IDs are not allowed"
    ),
    (
            "invalid_id",
            "IllegalField",
            "One or more members do not exist in this workspace or are not accessible"
    ),
    (
            "none_value",
            "IncorrectId",
            "All member IDs must be valid 24-character hex strings"
    )
])
def test_edit_task_member_custom_field_negative(
        owner_client,
        main_space,
        case_key,
        expected_code,
        expected_message
):
    """
    Member Custom Fields. Параметризованный негативный тест.
    Проверяет валидацию API при передаче некорректных данных:
    - duplicates: дублирующиеся ID участников.
    - invalid_id: несуществующий ID (24 hex char).
    - none_value: передача [None].
    """
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696e02e02452157dfd7e2577"

    # Генерация данных в зависимости от кейса
    if case_key == "duplicates":
        # Получаем реальный ID и дублируем его
        real_id = get_assignee(owner_client, main_space)[0]
        invalid_value = [real_id, real_id]
    elif case_key == "invalid_id":
        invalid_value = ["000000000000000000000000"]
    elif case_key == "none_value":
        invalid_value = [None]
    else:
        raise ValueError(f"Unknown case_key: {case_key}")

    with allure.step(f"Action: Отправка некорректных данных ({case_key}): {invalid_value}"):
        resp_edit = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=invalid_value
        ))

    with allure.step("Verification: Проверка структуры ошибки"):
        response_json = resp_edit.json()

        # Общая проверка структуры
        assert response_json.get("payload") is None
        assert response_json.get("type") == "EditTaskCustomField"

        error_data = response_json.get("error", {})
        assert error_data.get("code") == "InvalidForm"

        fields_errors = error_data.get("fields", [])
        assert len(fields_errors) > 0, "Массив ошибок fields пуст"

        field_error = fields_errors[0]
        assert field_error["name"] == "Member"
        assert expected_code in field_error["codes"]

        meta = field_error.get("meta", {})
        assert meta.get("message") == expected_message

        # Специфичные проверки meta
        if case_key == "duplicates":
            # Проверяем, что в received вернулись дубликаты
            assert sorted(meta.get("received")) == sorted(invalid_value)
        elif case_key == "none_value":
            # Проверяем invalidIds
            assert meta.get("invalidIds") == [None]