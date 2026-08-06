import pytest

from config.generators import generate_slug
from test_backend.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    get_spaces_endpoint,
    remove_space_endpoint,
)
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
