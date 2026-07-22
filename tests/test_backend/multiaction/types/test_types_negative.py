import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint
from test_backend.task_service.utils import get_two_random_types

pytestmark = [pytest.mark.backend]


def _get_task_types(client, space_id, task_id):
    """Получает список types задачи через GetTask."""
    r = client.post(**get_task_endpoint(space_id=space_id, slug_id=task_id))
    assert r.status_code == 200, r.text
    return r.json()["payload"]["task"].get("types", [])


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Negative")
@allure.title("Допустимые action только 'add' и 'remove' — 'toggle' отклоняется")
def test_invalid_action_toggle(owner_client, main_space, main_board, make_task_in_main):
    """
    types принимает только [typeId, 'add'] или [typeId, 'remove'].
    Любой другой action (например 'toggle') → 400.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_id = types[0][0]

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "toggle-type-action"})
        task_id = task["_id"]

    with allure.step("Отправляем types=[typeId, 'toggle']"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            types=[type_id, "toggle"],
        ))

    with allure.step("Проверяем, что API отклонил запрос"):
        assert resp.status_code == 400, (
            f"Ожидали 400 для невалидного action 'toggle', получили: {resp.status_code}"
        )

    with allure.step("Проверяем через GetTask, что тип не записался"):
        task_types = _get_task_types(owner_client, main_space, task_id)
        assert type_id not in task_types, (
            f"Тип записался несмотря на 400: {task_types}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Negative")
@allure.title("Два typeId в одном запросе")
def test_two_type_ids_in_single_request(owner_client, main_space, main_board, make_task_in_main):
    """
    Передаём [typeId1, typeId2, 'add'] — два typeId в одном запросе.
    Формат предполагает [typeId, action], длина массива != 2 → 400.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_id_1 = types[0][0]
    type_id_2 = types[1][0]

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "two-types-one-request"})
        task_id = task["_id"]

    with allure.step("Отправляем types=[typeId1, typeId2, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            types=[type_id_1, type_id_2, "add"],
        ))

    with allure.step("Проверяем, что API отклонил невалидный формат"):
        assert resp.status_code == 400, (
            f"Ожидали 400 для массива длиной != 2, получили: {resp.status_code}"
        )

    with allure.step("Проверяем через GetTask, что типы не записались"):
        task_types = _get_task_types(owner_client, main_space, task_id)
        assert type_id_1 not in task_types, (
            f"type_id_1 записался несмотря на 400: {task_types}"
        )
        assert type_id_2 not in task_types, (
            f"type_id_2 записался несмотря на 400: {task_types}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Negative")
@allure.title("Невалидный taskId + add type")
def test_add_type_invalid_task_id(owner_client, main_space, main_board, make_task_in_main):
    """
    Передаём валидный и несуществующий taskId с type add.
    Валидный — в success, невалидный — в failed.
    """
    types = get_two_random_types(owner_client, main_board, main_space)
    type_id = types[0][0]

    with allure.step("Создаём задачу и генерируем невалидный taskId"):
        task = make_task_in_main({"name": "valid-type-task"})
        valid_id = task["_id"]
        invalid_id = valid_id[:-1] + ("0" if valid_id[-1] != "0" else "1")

    with allure.step("Применяем MultipleEditTasks types add"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[valid_id, invalid_id],
            types=[type_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что валидный taskId в success"):
        assert payload["success"] == [valid_id], (
            f"Ожидали success=[{valid_id}], получили: {payload['success']}"
        )

    with allure.step("Проверяем, что невалидный taskId в failed"):
        assert payload["failed"] == [invalid_id], (
            f"Ожидали failed=[{invalid_id}], получили: {payload['failed']}"
        )

    with allure.step("Проверяем через GetTask, что type назначен"):
        task_types = _get_task_types(owner_client, main_space, valid_id)
        assert type_id in task_types, (
            f"type не назначен на валидную задачу: {task_types}"
        )


@allure.parent_suite("Multiaction")
@allure.suite("Types")
@allure.sub_suite("Negative")
@allure.title("Add несуществующий typeId — принимается без валидации")
def test_add_nonexistent_type_id(owner_client, main_space, make_task_in_main):
    """
    Передаём несуществующий typeId с action=add.
    MultipleEditTasks не валидирует существование typeId — ожидаемое поведение,
    т.к. валидация тяжёлая операция для массового эндпоинта.
    На фронте несуществующий тип не отображается.
    """
    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "nonexistent-type"})
        task_id = task["_id"]

    invalid_type_id = "000000000000000000000000"

    with allure.step("Применяем MultipleEditTasks types=[invalid_id, 'add']"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            types=[invalid_type_id, "add"],
        ))

    with allure.step("Проверяем контракт ответа"):
        # API не валидирует typeId — задача попадает в success
        assert resp.status_code == 200, f"Неожиданный статус: {resp.status_code}"
        payload = assert_multiaction_response(resp)
        assert payload["success"] == [task_id], (
            f"Ожидали success=[{task_id}], получили: {payload['success']}"
        )

    with allure.step("Несуществующий typeId записан в types"):
        task_types = _get_task_types(owner_client, main_space, task_id)
        assert invalid_type_id in task_types, (
            f"Поведение изменилось — невалидный typeId больше не в types: {task_types}"
        )
