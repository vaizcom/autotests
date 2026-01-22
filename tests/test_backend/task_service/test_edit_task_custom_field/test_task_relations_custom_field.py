import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint, get_task_endpoint

pytestmark = [pytest.mark.backend]


def _update_custom_field(client, space_id, task_id, field_id, value):
    """
    Вспомогательная функция для обновления значения кастомного поля.
    Возвращает объект ответа (Response).
    """
    return client.post(**edit_task_custom_field_endpoint(
        space_id=space_id,
        task_id=task_id,
        field_id=field_id,
        value=value
    ))


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Task Relations Custom Fields")
@allure.title("Edit Task Relations Custom Field. Проверка успешного обновления значения и очистки поля")
def test_edit_task_relations_custom_field(owner_client, main_space, board_with_tasks, main_project):
    """
    Task Relations Custom Fields. Проверка успешного обновления значения (массив ID) и очистки поля (пустой массив).
    """
    # Статические ID
    target_task_id = "696a1a04c7fd1dbba471efc2"
    relations_field_id = "696e02e42452157dfd7e25cd"

    # Значения для теста
    value_to_set = ["6971d6992452157dfd8076d4"]
    value_to_clear = []

    with allure.step("Pre-condition: Проверка и очистка поля перед тестом"):
        resp_pre = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_pre.status_code == 200

        task_pre = resp_pre.json().get("payload", {}).get("task")
        field_pre = next((cf for cf in task_pre.get("customFields", []) if cf.get("id") == relations_field_id), None)

        # Если поле найдено и не пустое — очищаем его используя хелпер
        if field_pre and field_pre.get("value"):
            _update_custom_field(owner_client, main_space, target_task_id, relations_field_id, value_to_clear)

    # 1. Установка значения
    with allure.step("Action: Установка значения в поле TaskRelations (массив ID)"):
        # Используем хелпер
        resp_set = _update_custom_field(owner_client, main_space, target_task_id, relations_field_id, value_to_set)

        assert resp_set.status_code == 200, f"Ошибка при установке значения: {resp_set.text}"

        task = resp_set.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа (значение установлено)"):
            updated_field = next((cf for cf in task["customFields"] if cf["id"] == relations_field_id), None)
            assert updated_field is not None, f"Поле {relations_field_id} не найдено в ответе"
            assert updated_field["value"] == value_to_set, \
                f"Значение поля не обновилось. Ожидалось: '{value_to_set}', получено: '{updated_field['value']}'"

            assert_task_payload(task, board_with_tasks, main_project)

    with allure.step("Post-condition: Проверка сохранения данных в БД (через GET Task)"):
        resp_after_set = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after_set.status_code == 200

        task_db = resp_after_set.json().get("payload", {}).get("task")
        field_db = next((cf for cf in task_db.get("customFields", []) if cf.get("id") == relations_field_id), None)

        assert field_db is not None
        assert field_db.get("value") == value_to_set, "Значение в БД не сохранилось после установки"

    # 2. Очистка значения
    with allure.step("Action: Очистка поля TaskRelations (передача пустого массива [])"):
        # Используем хелпер
        resp_clear = _update_custom_field(owner_client, main_space, target_task_id, relations_field_id, value_to_clear)

        assert resp_clear.status_code == 200, f"Ошибка при очистке значения: {resp_clear.text}"

        task_cleared = resp_clear.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа (значение очищено)"):
            cleared_field = next((cf for cf in task_cleared["customFields"] if cf["id"] == relations_field_id), None)
            assert cleared_field is not None
            assert cleared_field["value"] == value_to_clear, \
                f"Поле не очистилось. Ожидалось: [], получено: {cleared_field['value']}"

    with allure.step("Post-condition: Проверка очистки данных в БД (через GET Task)"):
        resp_after_clear = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after_clear.status_code == 200

        task_db_empty = resp_after_clear.json().get("payload", {}).get("task")
        field_db_empty = next(
            (cf for cf in task_db_empty.get("customFields", []) if cf.get("id") == relations_field_id), None)

        assert field_db_empty is not None
        assert field_db_empty.get("value") == value_to_clear, "Значение в БД не очистилось"


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Task Relations Custom Fields")
@allure.title("Edit Task Relations Custom Field. Multiple Values for ID задач из другого проекта")
def test_edit_task_relations_custom_field_multiple(owner_client, main_space, board_with_tasks, main_project):
    """
    Task Relations Custom Fields.
    1. Проверка установки массива из 3-х значений (ID задач из другого проекта).
    2. Проверка обновления массива (удаление одного элемента путем отправки списка из 2-х оставшихся).
    """
    # Статические ID
    target_task_id = "696a1a04c7fd1dbba471efc2"
    relations_field_id = "696e02e42452157dfd7e25cd"

    # Значения для теста (ID задач из другого проекта)
    # Исходный список из 3 ID
    initial_values = [
        "690af8691a593d8d7c4a8688",
        "690af86b1a593d8d7c4a86e9",
        "690af86d1a593d8d7c4a8740"
    ]

    # Новый список (удаляем последний элемент, оставляем первые два)
    updated_values = initial_values[:2]

    # Пустой список для очистки (если потребуется в pre-condition)
    empty_value = []

    with allure.step("Pre-condition: Проверка и очистка поля перед тестом"):
        resp_pre = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_pre.status_code == 200

        task_pre = resp_pre.json().get("payload", {}).get("task")
        field_pre = next((cf for cf in task_pre.get("customFields", []) if cf.get("id") == relations_field_id), None)

        if field_pre and field_pre.get("value"):
            _update_custom_field(owner_client, main_space, target_task_id, relations_field_id, empty_value)

    # 1. Установка 3-х значений
    with allure.step(f"Action: Установка 3-х значений в поле TaskRelations: {initial_values}"):
        resp_set = _update_custom_field(owner_client, main_space, target_task_id, relations_field_id, initial_values)
        assert resp_set.status_code == 200, f"Ошибка при установке значений: {resp_set.text}"

        task = resp_set.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа (все 3 значения установлены)"):
            updated_field = next((cf for cf in task["customFields"] if cf["id"] == relations_field_id), None)
            assert updated_field is not None
            # Сортируем списки перед сравнением, так как порядок может не гарантироваться
            assert sorted(updated_field["value"]) == sorted(initial_values), \
                f"Значения не совпали. Ожидалось: {initial_values}, получено: {updated_field['value']}"

            assert_task_payload(task, board_with_tasks, main_project)

    # 2. Обновление списка (удаление одного элемента)
    with allure.step(f"Action: Обновление поля (удаление одного элемента), отправляем: {updated_values}"):
        resp_update = _update_custom_field(owner_client, main_space, target_task_id, relations_field_id, updated_values)
        assert resp_update.status_code == 200, f"Ошибка при обновлении значений: {resp_update.text}"

        task_updated = resp_update.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа (осталось 2 значения)"):
            field_updated = next((cf for cf in task_updated["customFields"] if cf["id"] == relations_field_id), None)
            assert field_updated is not None
            assert len(field_updated["value"]) == 2, f"Ожидалось 2 элемента, получено {len(field_updated['value'])}"
            assert sorted(field_updated["value"]) == sorted(updated_values), \
                f"Значения не обновились корректно. Ожидалось: {updated_values}, получено: {field_updated['value']}"

    with allure.step("Post-condition: Проверка состояния в БД (через GET Task)"):
        resp_after = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after.status_code == 200

        task_db = resp_after.json().get("payload", {}).get("task")
        field_db = next((cf for cf in task_db.get("customFields", []) if cf.get("id") == relations_field_id), None)

        assert field_db is not None
        assert sorted(field_db.get("value")) == sorted(
            updated_values), "Значения в БД не соответствуют обновленному списку"


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Task Relations Custom Fields")
@pytest.mark.parametrize("case_name, invalid_value, expected_message", [
    (
            "Duplicate IDs",
            ["690af8691a593d8d7c4a8688", "690af86b1a593d8d7c4a86e9", "690af86b1a593d8d7c4a86e9"],
            "Duplicate task IDs are not allowed"
    ),
    (
            "Non-existent Task ID",
            ["000000000000000000000000"],  # Валидный формат (24 hex), но несуществующий ID
            "One or more tasks do not exist or are not accessible"
    ),
])
def test_edit_task_relations_custom_field_negative(owner_client, main_space, case_name, invalid_value,
                                                   expected_message):
    allure.dynamic.title(f"Edit Task Relations Custom Field. Negative: {case_name}")
    """
    Task Relations Custom Fields. Negative tests.
    Проверяет:
    1. Передачу дублей ID.
    2. Передачу несуществующего ID задачи.
    3. Передачу строки вместо массива.
    """
    allure.dynamic.title(f"Edit Task Relations Custom Field. Negative: {case_name}")

    target_task_id = "696a1a04c7fd1dbba471efc2"
    relations_field_id = "696e02e42452157dfd7e25cd"

    with allure.step(f"Action: Отправка некорректного значения: {invalid_value}"):
        resp_edit = _update_custom_field(
            owner_client,
            main_space,
            target_task_id,
            relations_field_id,
            invalid_value
        )

    with allure.step("Verification: Проверка ошибки валидации (InvalidForm)"):
        response_json = resp_edit.json()

        assert response_json["payload"] is None, "Payload должен быть null при ошибке валидации"
        assert response_json["type"] == "EditTaskCustomField"

        error_data = response_json.get("error", {})
        assert error_data.get("code") == "InvalidForm", \
            f"Ожидался код ошибки InvalidForm, получен {error_data.get('code')}"

        # Проверка деталей ошибки поля
        fields_errors = error_data.get("fields", [])
        assert len(fields_errors) > 0, "Список ошибок полей пуст"

        field_error = fields_errors[0]
        # # Имя поля в ошибке обычно "Linked Tasks"
        # assert field_error["name"] == "Linked Tasks"
        # assert "IllegalField" in field_error["codes"]

        meta = field_error.get("meta", {})
        assert meta.get("message") == expected_message, \
            f"Некорректное сообщение об ошибке. Ожидалось: '{expected_message}', получено: '{meta.get('message')}'"