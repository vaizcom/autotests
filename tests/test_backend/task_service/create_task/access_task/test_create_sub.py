import allure
import pytest

from test_backend.task_service.utils import get_client
from tests.test_backend.data.endpoints.Task.task_endpoints import (
    delete_task_endpoint, create_task_endpoint,
)

pytestmark = [pytest.mark.backend]

@allure.parent_suite("access_task")
@allure.title("Тестирование создания подзадачи разными пользовательскими ролями и проверка ожидаемого поведения")
@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_create_subtask_per_role(
    request, owner_client, main_space, main_board, create_task_in_main, client_fixture, expected_status
):
    """
    Тестирование создания подзадачи разными пользовательскими ролями и проверка
    ожидаемого поведения на основе прав доступа роли.

    Этот тест оценивает может ли клиент с разными уровнями доступа создавать
    подзадачу для родительской задачи. Также проверяются корректные связи между
    родительской задачей и подзадачей, включая поля `parentTask` и `subtasks`.
    """
    allure.dynamic.title(
        f"Тестирование создания подзадачи разными пользовательскими ролями: клиент={client_fixture}, ожидаемый статус={expected_status}"
    )
    client = get_client(request, client_fixture)
    parent_id = None
    subtask_id = None

    try:
        with allure.step("Создание родительской задачи через owner_client"):
            parent_req = create_task_endpoint(
                space_id=main_space,
                board=main_board,
                name="parent_task for subtask access test"
            )
            parent_resp = owner_client.post(**parent_req)
            assert parent_resp.status_code == 200, f"Не удалось создать родительскую задачу: {parent_resp.text}"
            parent_task = parent_resp.json()["payload"]["task"]
            parent_id = parent_task["_id"]

        with allure.step(f"Создание сабтаски в роли {client_fixture}"):
            subtask_req = create_task_endpoint(
                space_id=main_space,
                board=main_board,
                name=f"Subtask by {client_fixture}",
                parent_task=parent_id,
            )
            resp = client.post(**subtask_req)

            # Единая проверка статус-кода
            assert resp.status_code == expected_status, (
                f"Ожидали {expected_status}, получили {resp.status_code}: {getattr(resp, 'text', '')}"
            )

            if expected_status == 200:
                data = resp.json()
                subtask_task = data["payload"]["task"]
                subtask_id = subtask_task["_id"]
                assert subtask_id, f"{client_fixture} должен иметь возможность создать сабтаску"

                with allure.step("Проверяем, что в ответе у сабтаски присутствует parentTask с корректным ID."):
                    assert subtask_task.get("parentTask") == parent_id, (
                        f"У созданной сабтаски (ID={subtask_id}) поле parentTask должно быть {parent_id}, "
                        f"но сейчас: {subtask_task.get('parentTask')}"
                    )
                with allure.step("Проверяем что у сабтаски отсутствуют дочерние subtasks"):
                    assert subtask_task.get("subtasks", []) == [], (
                        f"Поле subtasks у сабтаски (ID={subtask_id}) должно быть пустым списком, "
                        f"но сейчас: {subtask_task.get('subtasks')}"
                    )
            else:  # expected_status == 403
                with allure.step(f"Проверяем, что {client_fixture} не может создать сабтаску (expected_status == 403)"):
                    body_text = getattr(resp, "text", "")
                    try:
                        data = resp.json()
                    except Exception:
                        pytest.fail(f"Ожидали JSON в ответе при 403, получили: {body_text}")

                    # payload должен быть None
                    assert data.get("payload") in (None,
                                                   {}), f"При отказе доступa payload должен отсутствовать/быть null, сейчас: {data.get('payload')}"

                    # проверяем структуру ошибки
                    err = data.get("error") or {}
                    assert isinstance(err, dict), f"Ожидали объект error, сейчас: {err}"
                    assert err.get(
                        "code") == "AccessDenied", f"Ожидали error.code == 'AccessDenied', сейчас: {err.get('code')}"
                    assert err.get("originalType") in (None,
                                                       "CreateTask"), f"Ожидали originalType 'CreateTask' или None, сейчас: {err.get('originalType')}"

    finally:
        if subtask_id:
            with allure.step(f"Удаляем сабтаску {subtask_id}"):
                del_resp = owner_client.post(**delete_task_endpoint(task_id=subtask_id, space_id=main_space))
                assert del_resp.status_code == 200, f"Не удалось удалить сабтаску {subtask_id}: {del_resp.text}"
        if parent_id:
            with allure.step(f"Удаляем родительскую задачу {parent_id}"):
                del_resp = owner_client.post(**delete_task_endpoint(task_id=parent_id, space_id=main_space))
                assert del_resp.status_code == 200, f"Не удалось удалить родителя {parent_id}: {del_resp.text}"