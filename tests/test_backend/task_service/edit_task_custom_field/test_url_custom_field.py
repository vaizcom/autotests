import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.task_service.conftest import _update_custom_field

pytestmark = [pytest.mark.backend]

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
    initial_value = "https://vaiz.com"
    value_to_set = "https://www.google.com"
    value_to_clear = ""

    with allure.step(f"Pre-condition: Установка начального значения {initial_value}"):
        resp_pre = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_pre.status_code == 200

        task_pre = resp_pre.json().get("payload", {}).get("task")
        field_pre = next((cf for cf in task_pre.get("customFields", []) if cf.get("id") == url_field_id), None)

        if field_pre and field_pre.get("value"):
            _update_custom_field(owner_client, main_space, target_task_id, url_field_id, initial_value)

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
@allure.title("Edit URL Custom Field. URL без протокола — бэкенд принимает и сохраняет.")
def test_edit_task_url_custom_field_no_protocol(owner_client, main_space):
    """
    URL без протокола (google.com) — бэкенд принимает и сохраняет как есть.
    Протокол подставляется на фронте при отображении.
    """
    target_task_id = "696a1a04c7fd1dbba471efc2"
    url_field_id = "696e02e92452157dfd7e2631"
    value_no_protocol = "google.com"

    with allure.step(f"Action: Отправка URL без протокола: {value_no_protocol}"):
        resp = _update_custom_field(owner_client, main_space, target_task_id, url_field_id, value_no_protocol)
        assert resp.status_code == 200, f"Ожидался 200, получен {resp.status_code}. Тело: {resp.text}"

    with allure.step("Verification: Проверка что значение сохранилось"):
        task = resp.json()["payload"]["task"]
        field = next((cf for cf in task["customFields"] if cf["id"] == url_field_id), None)
        assert field is not None, "Поле URL не найдено в ответе"
        assert field["value"] == value_no_protocol, \
            f"Ожидалось: '{value_no_protocol}', получено: '{field['value']}'"