import allure
import pytest

from test_backend.data.endpoints.Task.assert_task_payload import TASK_FULL_SCHEMA

pytestmark = [pytest.mark.backend]

def generate_immutable_field_params():
    """
    Генерирует параметры (field_name, invalid_value) для проверки неизменяемости полей.
    Использует TASK_FULL_SCHEMA как источник.
    Исключает поля из EDITABLE_FIELDS (те, что разрешено менять).
    Для остальных подбирает 'фейковые' значения правильного типа (чтобы пройти валидацию типов)
    и проверяет бизнес-логику (игнорирование изменений для неразрешенных полей в ответе).
    """
    # Белый список: поля, которые РАЗРЕШЕНО менять через EditTask
    EDITABLE_FIELDS = {
        "name", "completed", "assignees", "types",
        "dueStart", "dueEnd", "priority"
    }
    # Поля, которые меняются автоматически (side effects), поэтому их нельзя проверять на равенство с начальным состоянием
    VOLATILE_FIELDS = {
        "updatedAt"
    }

    params = []

    for field_name, field_type in TASK_FULL_SCHEMA.items():
        if field_name in EDITABLE_FIELDS or field_name in VOLATILE_FIELDS:
            continue

        # Определяем целевой тип для генерации значения
        target_type = field_type

        # Генерируем значение в зависимости от типа, чтобы не получить 400 Bad Request из-за типа,
        # а проверить именно невозможность записи в поле (200 OK, но поле старое).
        if field_name == "hrid":
            invalid_value = "ABCD"
        elif target_type is int:
            invalid_value = 9
        elif target_type is bool:
            invalid_value = True
        elif target_type is list:
            invalid_value = ["fake1","fake2"]
        elif target_type is dict:
            invalid_value = {"fake_key": "fake_value"}
        else:
            # Строки и прочее
            invalid_value = "6866731185fb8d104544fake"
            # Если поле похоже на дату, даем дату
            if "At" in field_name or "date" in field_name.lower():
                invalid_value = "2025-01-01T00:00:00.000Z"

        params.append((field_name, invalid_value))

    return params

immutable_params = generate_immutable_field_params()

@pytest.mark.parametrize(
    "field_name, invalid_value_to_set",
    immutable_params,
    ids=lambda val: str(val)
)
@allure.parent_suite("Task Service")
@allure.suite("Edit Task")
@allure.sub_suite("Negative cases edit Task")
@allure.title("Edit Task: НЕГАТИВНЫЙ ТЕСТ - Поле '{field_name}' не должно меняться")
def test_edit_task_immutable_field_cannot_be_changed1(owner_client, main_space, make_task_in_main, main_board,
                                                      field_name, invalid_value_to_set):
    """
    Проверяет, что при попытке изменить указанное поле через эндпоинт EditTask,
    его значение в ответе API остается неизменным (таким же, как и у исходной задачи).

    Этот тест предназначен для выявления бага, когда поле перезаписывается,
    хотя это недопустимо для данного эндпоинта.
    """
    # 1. Создаем начальную задачу
    initial_task_data = make_task_in_main({
        "name": f"Task to test {field_name} immutability"
    })
    task_id = initial_task_data.get("_id")
    initial_field_value = initial_task_data.get(field_name)

    value_to_send = invalid_value_to_set

    with allure.step(
            f"Попытка изменить поле '{field_name}' задачи {task_id} с {initial_field_value!r} на {value_to_send!r}"):
        request_json_body = {
            "taskId": task_id,
            field_name: value_to_send
        }
        resp = owner_client.post(
            path="/EditTask",
            json=request_json_body,
            headers={
                "Content-Type": "application/json",
                "Current-Space-Id": main_space,
            },
        )

    with allure.step("Проверяем статус ответа и тело"):
        assert resp.status_code == 200, \
            f"Ожидался статус 200, но получен {resp.status_code}. Ответ: {resp.text}"

        body = resp.json()
        updated_task = body.get("payload", {}).get("task")
        assert updated_task is not None, "Payload или Task отсутствуют в ответе"
        assert updated_task.get("_id") == task_id

    with allure.step(f"Проверяем, что поле '{field_name}' НЕ БЫЛО изменено"):
        final_field_value = updated_task.get(field_name)

        # Проверка 1: Значение должно быть равно начальному
        assert final_field_value == initial_field_value, \
            f"БАГ: Неизменяемое поле '{field_name}' изменилось! " \
            f"Было: {initial_field_value!r}, Стало: {final_field_value!r}. " \
            f"Попытка записи: {value_to_send!r}"

        # Проверка 2: Значение точно не равно тому, что мы пытались записать
        if initial_field_value != value_to_send:
            assert final_field_value != value_to_send, \
                f"БАГ: Поле '{field_name}' перезаписалось переданным значением: {value_to_send!r}."