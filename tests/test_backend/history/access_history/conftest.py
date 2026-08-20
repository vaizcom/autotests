import pytest

from config.generators import generate_date
from core.response_utils import short_resp
from test_backend.data.endpoints.Board.board_endpoints import (
    get_boards_endpoint,
    delete_board_endpoint,
)
from test_backend.data.endpoints.Board.constants import DEFAULT_BOARD_GROUPS, typesList
from test_backend.data.endpoints.Project.project_endpoints import create_board_endpoint
from test_backend.data.endpoints.Task.task_endpoints import (
    create_task_endpoint,
    delete_task_endpoint,
)
from test_backend.data.endpoints.milestone.milestones_endpoints import (
    create_milestone_endpoint,
    archive_milestone_endpoint,
    get_milestones_endpoint,
)

# ──────────────────────────────────────────────────────────────────────────────
# Существующий майлстоун на main_board (для roles теста)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def milestone_id_on_main_board(owner_client, main_space, main_board):
    """Возвращает ID первого существующего майлстоуна на main_board."""
    resp = owner_client.post(**get_milestones_endpoint(
        space_id=main_space, board_id=main_board, limit=1,
    ))
    assert resp.status_code == 200, f"Ошибка GetMilestones: {short_resp(resp)}"
    milestones = resp.json().get("payload", {}).get("milestones", [])
    assert len(milestones) > 0, "На main_board нет майлстоунов"
    return milestones[0]["_id"]


# ──────────────────────────────────────────────────────────────────────────────
# Борда / Задача / Майлстоун в temp_main_project_2 (для кросс-проект изоляции)
# ──────────────────────────────────────────────────────────────────────────────

_TEMP_BOARD_PROJECT_2 = "_autotest_temp_board_project_2"


@pytest.fixture(scope="session")
def temp_board_in_project_2(owner_client, main_space, temp_main_project_2):
    """Временная борда в temp_main_project_2 для тестов кросс-проект изоляции."""
    # Cleanup: удаляем мусор от предыдущего прогона
    resp = owner_client.post(**get_boards_endpoint(space_id=main_space))
    if resp.status_code == 200:
        for board in resp.json().get("payload", {}).get("boards", []):
            if board.get("name") == _TEMP_BOARD_PROJECT_2:
                owner_client.post(**delete_board_endpoint(
                    board_id=board["_id"],
                    board_name=_TEMP_BOARD_PROJECT_2,
                    space_id=main_space,
                ))

    resp = owner_client.post(**create_board_endpoint(
        name=_TEMP_BOARD_PROJECT_2,
        temp_project=temp_main_project_2,
        space_id=main_space,
        groups=DEFAULT_BOARD_GROUPS,
        typesList=typesList,
        customFields=[],
    ))
    assert resp.status_code == 200, f"Ошибка создания борды в project_2: {resp.text}"
    board_id = resp.json()["payload"]["board"]["_id"]

    yield board_id

    owner_client.post(**delete_board_endpoint(
        board_id=board_id,
        board_name=_TEMP_BOARD_PROJECT_2,
        space_id=main_space,
    ))


@pytest.fixture
def temp_task_in_project_2(owner_client, main_space, temp_board_in_project_2):
    """Временная задача на борде в project_2."""
    resp = owner_client.post(**create_task_endpoint(
        space_id=main_space,
        board=temp_board_in_project_2,
        name="Temp task in project_2 for isolation",
    ))
    assert resp.status_code == 200, f"Ошибка создания задачи: {short_resp(resp)}"
    task_id = resp.json()["payload"]["task"]["_id"]

    yield task_id

    del_resp = owner_client.post(**delete_task_endpoint(space_id=main_space, task_id=task_id))
    if del_resp.status_code not in (200, 400, 404):
        pytest.fail(f"Ошибка удаления задачи: {short_resp(del_resp)}")


@pytest.fixture
def temp_milestone_in_project_2(owner_client, main_space, temp_board_in_project_2, temp_main_project_2):
    """Временный майлстоун на борде в project_2."""
    resp = owner_client.post(**create_milestone_endpoint(
        space_id=main_space,
        board=temp_board_in_project_2,
        name="Temp Milestone project_2 " + generate_date(),
        project=temp_main_project_2,
    ))
    assert resp.status_code == 200, f"Ошибка создания майлстоуна: {short_resp(resp)}"
    milestone_id = resp.json()["payload"]["milestone"]["_id"]

    yield milestone_id

    archive_resp = owner_client.post(**archive_milestone_endpoint(
        space_id=main_space, milestone_id=milestone_id,
    ))
    if archive_resp.status_code not in (200, 400, 404):
        pytest.fail(f"Ошибка архивации майлстоуна: {short_resp(archive_resp)}")


