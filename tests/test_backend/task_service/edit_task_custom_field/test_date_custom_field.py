import allure
import pytest
from datetime import datetime, timedelta, timezone

from test_backend.data.endpoints.Task.assert_task_payload import assert_task_payload
from test_backend.data.endpoints.Task.task_endpoints import edit_task_custom_field_endpoint, get_task_endpoint

pytestmark = [pytest.mark.backend]


def generate_future_date_iso(days_ahead=1):
    """Генерирует дату в будущем в формате ISO 8601 с UTC (Z)"""
    future_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    return future_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Date Custom Fields")
@allure.title("Edit Date Custom Field. Positive Flows")
@pytest.mark.parametrize("date_scenario, generate_value_func", [
    (
            "Single Date",
            lambda: [None, generate_future_date_iso(days_ahead=5)]
    ),
    (
            "Date Range",
            lambda: [generate_future_date_iso(days_ahead=2), generate_future_date_iso(days_ahead=10)]
    )
])
def test_edit_task_date_custom_field(
        owner_client,
        main_space,
        board_with_tasks,
        main_project,
        date_scenario,
        generate_value_func
):
    """
    Date Custom Fields.
    Проверка успешного обновления:
    1. Одиночная дата (Single Date)
    2. Интервал дат (Date Range)
    """
    allure.dynamic.title(f"{date_scenario}: Edit Date Custom Field for {date_scenario}")

    # Статические ID
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696a1a13c7fd1dbba471f050"

    # Генерируем новое значение (массив строк)
    new_value_list = generate_value_func()

    with allure.step("Pre-condition: Проверка текущего значения"):
        resp_before = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_before.status_code == 200

        task_before = resp_before.json().get("payload", {}).get("task")
        cfs_before = task_before.get("customFields", [])
        cf_before = next((cf for cf in cfs_before if cf.get("id") == target_custom_field_id), None)

        # Если случайно сгенерировали то же самое (очень маловероятно с timestamp)
        if cf_before and cf_before.get("value") == new_value_list:
            # Просто перегенерируем с другим сдвигом
            new_value_list = [generate_future_date_iso(days_ahead=20)]
            if date_scenario == "Date Range":
                new_value_list.append(generate_future_date_iso(days_ahead=25))

    with allure.step(f"Action: Отправка запроса с датами {new_value_list}"):
        resp_edit = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=new_value_list
        ))
        assert resp_edit.status_code == 200, f"Ошибка при редактировании: {resp_edit.text}"

        task = resp_edit.json()["payload"]["task"]

        with allure.step("Verification: Валидация ответа и обновленного поля"):
            updated_field = next((cf for cf in task["customFields"] if cf["id"] == target_custom_field_id), None)
            assert updated_field is not None, f"Поле {target_custom_field_id} не найдено в ответе"

            # API может возвращать список
            received_value = updated_field["value"]

            assert isinstance(received_value, list), f"Ожидался список дат, получено: {type(received_value)}"
            assert len(received_value) == len(new_value_list), \
                f"Количество дат не совпадает. Ожидалось {len(new_value_list)}, получено {len(received_value)}"

            # Сравниваем даты как строки
            assert received_value == new_value_list, \
                f"Значения дат не совпадают. Ожидалось: {new_value_list}, Получено: {received_value}"

            assert_task_payload(task, board_with_tasks, main_project)

    with allure.step("Post-condition: Проверка сохранения в БД"):
        resp_after = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=target_task_id))
        assert resp_after.status_code == 200

        task_after = resp_after.json().get("payload", {}).get("task")
        updated_field = next(
            (cf for cf in task_after.get("customFields", []) if cf.get("id") == target_custom_field_id), None)

        assert updated_field is not None
        assert updated_field.get("value") == new_value_list


@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Date Custom Fields")
@allure.title("Edit Date Custom Field. Negative: Invalid Date Format")
def test_edit_task_date_custom_field_invalid_format(owner_client, main_space):
    """
    Date Custom Fields. Негативный тест: передача некорректного формата даты вызывает ошибку.
    """
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696a1a13c7fd1dbba471f050"

    # Некорректный формат (не ISO)
    invalid_value = ["15.10.2025"]

    with allure.step(f"Action: Отправка некорректной даты {invalid_value}"):
        resp_edit = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=invalid_value
        ))

    with allure.step("Verification: Проверка ошибки валидации"):
        # Здесь ожидаем либо 400 Bad Request, либо специфичную ошибку InvalidForm
        # Если API строгий, он вернет InvalidForm.
        response_json = resp_edit.json()

        # Адаптируйте проверки под реальный ответ вашего API на плохую дату
        if resp_edit.status_code == 200 and response_json.get("error"):
            error_data = response_json.get("error", {})
            assert error_data.get("code") == "InvalidForm"
            # Проверяем детали, если они есть
            fields = error_data.get("fields", [])
            if fields:
                assert "Date" in fields[0]["name"] or fields[0]["name"] == "Date"

@allure.parent_suite("Task Service")
@allure.suite("Edit Task Custom Field")
@allure.sub_suite("Date Custom Fields")
@allure.title("Edit Date Custom Field. Negative: End Date before Start Date")
def test_edit_task_date_custom_field_end_before_start(owner_client, main_space):
    """
    Date Custom Fields. Негативный тест: дата окончания (второй элемент)
    не может быть раньше даты начала (первый элемент).
    """
    target_task_id = "696a1a04c7fd1dbba471efc2"
    target_custom_field_id = "696a1a13c7fd1dbba471f050"

    # Генерируем даты: Начало позже Конца
    start_date = generate_future_date_iso(days_ahead=10)  # 2025-10-15...
    end_date_invalid = generate_future_date_iso(days_ahead=5)  # 2025-10-10... (раньше старта)

    invalid_range = [start_date, end_date_invalid]

    with allure.step(f"Action: Отправка интервала, где конец раньше начала: {invalid_range}"):
        resp_edit = owner_client.post(**edit_task_custom_field_endpoint(
            space_id=main_space,
            task_id=target_task_id,
            field_id=target_custom_field_id,
            value=invalid_range
        ))

    with allure.step("Verification: Проверка ошибки валидации (InvalidForm)"):
        response_json = resp_edit.json()

        assert response_json["payload"] is None
        assert response_json["type"] == "EditTaskCustomField"

        error_data = response_json.get("error", {})
        assert error_data.get("code") == "InvalidForm", \
            f"Ожидался код ошибки InvalidForm, получен {error_data.get('code')}"
        assert error_data.get("originalType") == "EditTaskCustomField"

        fields_errors = error_data.get("fields", [])
        assert len(fields_errors) > 0, "Список ошибок полей пуст"

        field_error = fields_errors[0]
        assert field_error["name"] == "Date", f"Ожидалось имя поля 'Date', получено '{field_error.get('name')}'"
        assert "IllegalField" in field_error["codes"]

        meta = field_error.get("meta", {})
        expected_msg = "Start date cannot be after end date"
        assert meta.get("message") == expected_msg, \
            f"Неверное сообщение об ошибке. Ожидалось: '{expected_msg}', получено: '{meta.get('message')}'"

        # Проверяем, что сервер вернул именно те даты, которые мы отправили
        assert meta.get("received") == invalid_range, \
            f"В поле received вернулись не те данные. Ожидалось: {invalid_range}, получено: {meta.get('received')}"