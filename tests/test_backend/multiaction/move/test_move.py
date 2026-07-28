import allure
import pytest

from config.generators import generate_object_id
from test_backend.data.endpoints.multiaction.multiaction_endpoints import multiple_move_tasks_endpoint
from test_backend.data.endpoints.multiaction.multiaction_asserts import assert_multiaction_response
from test_backend.data.endpoints.Task.task_endpoints import get_task_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Multiaction")
@allure.suite("Move")
@allure.sub_suite("Positive")
@allure.title("Move: переместить задачи в другую группу")
def test_move_tasks_to_another_group(
    owner_client, main_space, make_task_in_main, temp_board_in_main, board_groups,
):
    """MultipleMoveTasks перемещает задачи между группами внутри одной борды."""
    target_group = board_groups["Todo"]

    with allure.step("Создаём 2 задачи (попадают в Backlog)"):
        tasks = [make_task_in_main({"name": f"move-test-{i}", "board": temp_board_in_main}) for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    with allure.step("Перемещаем в группу Todo"):
        resp = owner_client.post(**multiple_move_tasks_endpoint(
            space_id=main_space, tasks_ids=task_ids,
            board_id=temp_board_in_main, to_group_id=target_group,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids)
        assert payload["failed"] == []
        assert payload["skipped"] == []

    with allure.step("Проверяем через GetTask, что задачи в группе Todo"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200, r.text
            task = r.json()["payload"]["task"]
            assert task["group"] == target_group, f"Задача {tid} не в целевой группе"


@allure.parent_suite("Multiaction")
@allure.suite("Move")
@allure.sub_suite("Positive")
@allure.title("Move: задача уже в целевой группе → skipped")
def test_move_already_in_target_group_skipped(
    owner_client, main_space, make_task_in_main, temp_board_in_main, board_groups,
):
    target_group = board_groups["Backlog"]

    with allure.step("Создаём задачу (по умолчанию в Backlog)"):
        task = make_task_in_main({"name": "move-skip", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Пытаемся переместить в ту же группу Backlog"):
        resp = owner_client.post(**multiple_move_tasks_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            board_id=temp_board_in_main, to_group_id=target_group,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что задача в skipped"):
        assert payload["skipped"] == [task_id]
        assert payload["success"] == []


@allure.parent_suite("Multiaction")
@allure.suite("Move")
@allure.sub_suite("Positive")
@allure.title("Move: mixed — часть уже в целевой группе, часть нет")
def test_move_mixed_state(
    owner_client, main_space, make_task_in_main, temp_board_in_main, board_groups,
):
    target_group = board_groups["In Progress"]

    with allure.step("Создаём задачу в Backlog и перемещаем одну в In Progress заранее"):
        task_backlog = make_task_in_main({"name": "move-mix-bl", "board": temp_board_in_main})
        task_inprog = make_task_in_main({"name": "move-mix-ip", "board": temp_board_in_main})
        # Перемещаем вторую в целевую группу заранее
        owner_client.post(**multiple_move_tasks_endpoint(
            space_id=main_space, tasks_ids=[task_inprog["_id"]],
            board_id=temp_board_in_main, to_group_id=target_group,
        ))

    with allure.step("Перемещаем обе в In Progress"):
        all_ids = [task_backlog["_id"], task_inprog["_id"]]
        resp = owner_client.post(**multiple_move_tasks_endpoint(
            space_id=main_space, tasks_ids=all_ids,
            board_id=temp_board_in_main, to_group_id=target_group,
        ))

    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем: backlog в success, inprog в skipped"):
        assert task_backlog["_id"] in payload["success"]
        assert task_inprog["_id"] in payload["skipped"]
        assert payload["failed"] == []


@allure.parent_suite("Multiaction")
@allure.suite("Move")
@allure.sub_suite("Negative")
@allure.title("Move: невалидный to_group_id → ошибка")
def test_move_invalid_group_id(
    owner_client, main_space, make_task_in_main, temp_board_in_main,
):
    fake_group_id = generate_object_id()

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "move-neg-group", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Перемещаем с несуществующей группой"):
        resp = owner_client.post(**multiple_move_tasks_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            board_id=temp_board_in_main, to_group_id=fake_group_id,
        ))

    with allure.step("Проверяем ошибку 400 IncorrectToGroupId"):
        assert resp.status_code == 400, f"Ожидали 400, получили {resp.status_code}"
        error = resp.json().get("error", {})
        assert error.get("code") == "IncorrectToGroupId", f"Ожидали IncorrectToGroupId, получили: {error}"


@allure.parent_suite("Multiaction")
@allure.suite("Move")
@allure.sub_suite("Negative")
@allure.title("Move: нет доступа к спейсу → 400 MemberDidNotFound")
def test_move_no_access_to_space(
    foreign_client, owner_client, main_space, make_task_in_main,
    temp_board_in_main, board_groups,
):
    target_group = board_groups["Todo"]

    with allure.step("Создаём задачу (от owner)"):
        task = make_task_in_main({"name": "move-neg-access", "board": temp_board_in_main})
        task_id = task["_id"]

    with allure.step("Перемещаем от foreign_client"):
        resp = foreign_client.post(**multiple_move_tasks_endpoint(
            space_id=main_space, tasks_ids=[task_id],
            board_id=temp_board_in_main, to_group_id=target_group,
        ))

    with allure.step("Проверяем ошибку 400 MemberDidNotFound"):
        assert resp.status_code == 400, f"Ожидали 400, получили {resp.status_code}"
        error = resp.json().get("error", {})
        assert error.get("code") == "MemberDidNotFound", f"Ожидали MemberDidNotFound, получили: {error}"
