import pytest

from config.generators import generate_slug
from config.settings import USERS
from test_backend.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    get_spaces_endpoint,
    remove_space_endpoint,
)
from test_backend.data.endpoints.invite.invite_endpoint import (
    invite_to_space_endpoint,
    confirm_space_invite_endpoint,
)
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from test_backend.data.endpoints.Project.project_endpoints import (
    create_project_endpoint,
    create_board_endpoint,
)
from test_backend.data.endpoints.Board.constants import DEFAULT_BOARD_GROUPS

_SPACE_FOR_HISTORY = "_autotest_history_space"


@pytest.fixture(scope="session")
def space_for_history(main_client):
    """
    Создаёт чистый space для проверки history-событий.
    Возвращает dict с space_id и начальным именем.
    Один space на все тесты папки space_events, удаляется после завершения сессии.
    """
    # Cleanup: удаляем мусор от предыдущего прогона
    resp = main_client.post(**get_spaces_endpoint())
    if resp.status_code == 200:
        for space in resp.json().get("payload", {}).get("spaces", []):
            if space.get("name") == _SPACE_FOR_HISTORY:
                main_client.post(**remove_space_endpoint(space_id=space["_id"]))

    resp = main_client.post(**create_space_endpoint(name=_SPACE_FOR_HISTORY))
    assert resp.status_code == 200, f"Setup: не удалось создать space_for_history: {resp.text}"
    space_id = resp.json()["payload"]["space"]["_id"]

    yield {"space_id": space_id, "name": _SPACE_FOR_HISTORY}

    main_client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope="session")
def project_for_history(main_client, space_for_history):
    """Проект в space_for_history для тестов событий с kind=Project."""
    space_id = space_for_history["space_id"]
    name = "_autotest_history_project"
    slug = generate_slug()
    resp = main_client.post(**create_project_endpoint(
        name=name, slug=slug, color="blue", icon="Dot",
        description="history event test project", space_id=space_id,
    ))
    assert resp.status_code == 200, f"Setup: не удалось создать project_for_history: {resp.text}"
    project_id = resp.json()["payload"]["project"]["_id"]
    yield {"project_id": project_id, "name": name}


@pytest.fixture(scope="session")
def board_for_history(main_client, space_for_history, project_for_history):
    """Борда в project_for_history для тестов событий с kind=Board."""
    space_id = space_for_history["space_id"]
    project_id = project_for_history["project_id"]
    name = "_autotest_history_board"
    resp = main_client.post(**create_board_endpoint(
        name=name, temp_project=project_id, space_id=space_id,
        groups=DEFAULT_BOARD_GROUPS, typesList=[], customFields=[],
    ))
    assert resp.status_code == 200, f"Setup: не удалось создать board_for_history: {resp.text}"
    board_id = resp.json()["payload"]["board"]["_id"]
    yield {"board_id": board_id, "name": name}


@pytest.fixture(scope="session")
def manager_in_space(main_client, manager_client, space_for_history):
    """
    Приглашает manager в space_for_history и возвращает member_id.
    Если manager уже в спейсе — просто находит его member_id.
    """
    space_id = space_for_history["space_id"]
    manager_email = USERS["manager"]["email"]
    manager_password = USERS["manager"]["password"]

    invite_resp = main_client.post(**invite_to_space_endpoint(
        space_id=space_id,
        email=manager_email,
        space_access="Manager",
    ))
    if invite_resp.status_code == 200:
        spaces_resp = manager_client.post(**get_spaces_endpoint())
        assert spaces_resp.status_code == 200
        spaces = spaces_resp.json().get("payload", {}).get("spaces", [])
        target = next((s for s in spaces if s.get("_id") == space_id), None)
        assert target is not None, f"Setup: space {space_id} не найден у manager"
        confirm_resp = manager_client.post(**confirm_space_invite_endpoint(
            code=target["inviteCode"],
            full_name="manager",
            password=manager_password,
            termsAccepted=True,
        ))
        assert confirm_resp.status_code == 200, f"Setup: ошибка принятия инвайта: {confirm_resp.text}"

    members_resp = main_client.post(**get_space_members_endpoint(space_id=space_id))
    assert members_resp.status_code == 200
    members = members_resp.json()["payload"]["members"]
    manager_member = next((m for m in members if m.get("email") == manager_email), None)
    assert manager_member is not None, f"Setup: manager ({manager_email}) не найден в участниках"

    yield {"member_id": manager_member["_id"], "email": manager_email}
