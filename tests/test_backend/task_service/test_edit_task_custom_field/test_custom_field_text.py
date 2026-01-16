import allure
import pytest
import uuid

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint, get_task_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Text Custom Fields")
@allure.title("Edit Text Custom Field. Positive Flows")
def test_edit_task_text_custom_field(owner_client, main_space, board_with_tasks, main_project):
    """
    Text Custom Fields. Проверка успешного обновления значения текстового кастомного поля.
    """
    # Статические ID
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696a1a0ac7fd1dbba471f014"

    # Генерируем уникальное значение
    new_value = f"Val-{uuid.uuid4().hex[:6]}"

    with allure.step("Pre-condition: Получение текущего состояния задачи и его значений в customFields (через GET Task) "):
        resp_before = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_before.status_code == 200, "Не удалось получить задачу перед тестом"

        task_before = resp_before.json().get("payload", {}).get("task")
        cfs_before = task_before.get("customFields", [])

        # Находим поле в списке словарей
        cf_before = next((cf for cf in cfs_before if cf.get("id") == target_custom_field_id), None)
        assert cf_before is not None, f"Кастомное поле {target_custom_field_id} не найдено в задаче перед тестом"

        if cf_before:
            assert cf_before.get("value") != new_value, \
                "Текущее значение в базе уже совпадает с новым! Тест неэффективен."

    with allure.step(f"Action: Отправка запроса на изменение поля Text"):
        resp_edit = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=new_value
        ))
        assert resp_edit.status_code == 200, f"Ошибка при редактировании: {resp_edit.text}"

        task = resp_edit.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа и обновленного поля"):
            assert task.get("_id") == target_task_id

            # Поиск словаря с нужным ID
            updated_field = next((cf for cf in task["customFields"] if cf["id"] == target_custom_field_id), None)

            assert updated_field is not None, f"Поле {target_custom_field_id} не найдено в ответе"
            assert updated_field["value"] == new_value, \
                f"Значение поля не обновилось. Ожидалось: '{new_value}', получено: '{updated_field['value']}'"

            # Полная проверка структуры задачи
            assert_task_payload(task, board_with_tasks, main_project)

    with allure.step("Post-condition: Проверка сохранения данных в БД (через GET Task)"):
        resp_after = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after.status_code == 200

        task_after = resp_after.json().get("payload", {}).get("task")
        cfs_after = task_after.get("customFields", [])

        updated_field = next((cf for cf in cfs_after if cf.get("id") == target_custom_field_id), None)

        assert updated_field is not None, "Кастомное поле не найдено в задаче после обновления"
        assert updated_field.get("value") == new_value, \
            f"Значение в БД не сохранилось! Ожидалось '{new_value}', получено '{updated_field.get('value')}'"