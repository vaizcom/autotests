import time

import allure
import pytest

from config.settings import USERS
from test_backend.data.endpoints.Task.task_endpoints import create_task_endpoint, delete_task_endpoint
from test_backend.data.endpoints.milestone.milestones_endpoints import create_milestone_endpoint, archive_milestone_endpoint
from test_backend.data.endpoints.Project.project_endpoints import create_board_endpoint
from test_backend.data.endpoints.Board.constants import DEFAULT_BOARD_GROUPS
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint


@pytest.fixture
def temp_task(main_client, space_for_history, board_for_history):
    """Временная задача на board_for_history. Создаётся перед тестом, удаляется после.
    Добавлять pre-cleanup для каждой временной сущности — лишний код.
    Достаточно каскада удаления в space_for_history"""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    with allure.step("Setup: создаём временную задачу"):
        # Ретрай на случай MemberDidNotFound — в CI мембер может быть ещё не проиндексирован
        for attempt in range(5):
            resp = main_client.post(**create_task_endpoint(
                space_id=space_id, board=board_id, name="Temp task for history events"
            ))
            if resp.status_code == 200:
                break
            error_code = resp.json().get("error", {}).get("code", "")
            if error_code == "MemberDidNotFound" and attempt < 4:
                time.sleep(2)
                continue
            break
        assert resp.status_code == 200, f"Setup: не удалось создать задачу: {resp.text}"
        task_id = resp.json()["payload"]["task"]["_id"]

    yield task_id

    with allure.step("Teardown: удаляем временную задачу"):
        resp = main_client.post(**delete_task_endpoint(space_id=space_id, task_id=task_id))
        # 400/404 — задача могла быть удалена или конвертирована в самом тесте
        assert resp.status_code in (200, 400, 404), f"Teardown: ошибка удаления задачи: {resp.text}"


@pytest.fixture
def temp_milestone(main_client, space_for_history, board_for_history, project_for_history):
    """Временный майлстоун на board_for_history. Создаётся перед тестом, архивируется после."""
    space_id = space_for_history["space_id"]
    board_id = board_for_history["board_id"]
    with allure.step("Setup: создаём временный майлстоун"):
        resp = main_client.post(**create_milestone_endpoint(
            space_id=space_id, board=board_id, name="Temp milestone for history events",
            project=project_for_history["project_id"],
        ))
        assert resp.status_code == 200, f"Setup: не удалось создать майлстоун: {resp.text}"
        milestone_id = resp.json()["payload"]["milestone"]["_id"]

    yield milestone_id

    with allure.step("Teardown: архивируем майлстоун"):
        main_client.post(**archive_milestone_endpoint(space_id=space_id, milestone_id=milestone_id))


@pytest.fixture(scope="session")
def second_board(main_client, space_for_history, project_for_history):
    """Вторая борда в project_for_history для тестов перемещения между бордами."""
    space_id = space_for_history["space_id"]
    project_id = project_for_history["project_id"]
    resp = main_client.post(**create_board_endpoint(
        name="_autotest_history_board_2", temp_project=project_id, space_id=space_id,
        groups=DEFAULT_BOARD_GROUPS, typesList=[], customFields=[],
    ))
    assert resp.status_code == 200, f"Setup: не удалось создать вторую борду: {resp.text}"
    yield resp.json()["payload"]["board"]["_id"]



@pytest.fixture(scope="session")
def history_members(main_client, space_for_history, manager_in_space):
    """Словарь member_id участников space_for_history по ролям."""
    space_id = space_for_history["space_id"]
    resp = main_client.post(**get_space_members_endpoint(space_id=space_id))
    assert resp.status_code == 200
    members = resp.json()["payload"]["members"]

    main_email = USERS["main"]["email"]
    main_ids = [m["_id"] for m in members if m.get("email") == main_email]
    manager_ids = [manager_in_space["member_id"]]

    return {"main": main_ids, "manager": manager_ids}
