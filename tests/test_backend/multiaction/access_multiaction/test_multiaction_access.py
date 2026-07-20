import allure
import pytest

from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_edit_tasks_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Multiaction")
@allure.suite("Access")
@allure.title("Проверка прав на MultipleEditTasks клиентом: {client_fixture}")
@pytest.mark.parametrize(
    "client_fixture, expect_success",
    [
        ("owner_client", True),
        ("manager_client", True),
        ("member_client", True),
        ("guest_client", False),
        ("client_with_access_only_in_project", False),
    ],
    ids=["owner", "manager", "member", "guest", "no_board_access"],
)
def test_multiaction_access_by_role(request, client_fixture, expect_success, main_space, make_task_in_main):
    """
    Owner, Manager, Member — задача в success.
    Guest, пользователь без доступа к борде — задача в failed.
    """
    client = request.getfixturevalue(client_fixture)

    with allure.step("Создаём незавершённую задачу от owner"):
        task = make_task_in_main({"name": f"access_multiaction-{client_fixture}", "completed": False})
        task_id = task["_id"]

    with allure.step(f"Отправляем MultipleEditTasks от {client_fixture}"):
        resp = client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[task_id],
            completed=True,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    if expect_success:
        with allure.step("Проверяем, что задача в success"):
            assert payload["success"] == [task_id], (
                f"Ожидали success=[{task_id}], получили: {payload['success']}"
            )
            assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
    else:
        with allure.step("Проверяем, что задача в failed"):
            assert payload["failed"] == [task_id], (
                f"Ожидали failed=[{task_id}], получили: {payload['failed']}"
            )
            assert payload["success"] == [], f"success не пуст: {payload['success']}"


# ---------------------------------------------------------------------------
#  Задачи на разных бордах — все в success
# ---------------------------------------------------------------------------

@allure.parent_suite("Multiaction")
@allure.suite("Access")
@allure.title("Задачи на разных бордах — все в success")
def test_cross_board_tasks(owner_client, main_space, make_task_in_main, temp_board_in_main):
    """
    Задачи созданы на разных бордах в одном space.
    API обрабатывает их все, boardId не ограничивает multiaction.
    """
    with allure.step("Создаём задачу на main_board"):
        t1 = make_task_in_main({"name": "cross-board-1", "completed": False})

    with allure.step("Создаём задачу на временной борде"):
        t2 = make_task_in_main({"name": "cross-board-2", "completed": False, "board": temp_board_in_main})

    with allure.step("Применяем MultipleEditTasks completed=True к обеим"):
        resp = owner_client.post(**multiple_edit_tasks_endpoint(
            space_id=main_space,
            tasks_ids=[t1["_id"], t2["_id"]],
            completed=True,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что обе задачи в success"):
        assert sorted(payload["success"]) == sorted([t1["_id"], t2["_id"]]), (
            f"Ожидали обе задачи в success, получили: {payload['success']}"
        )
        assert payload["failed"] == [], f"failed не пуст: {payload['failed']}"
