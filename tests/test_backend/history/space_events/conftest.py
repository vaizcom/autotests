import pytest

from test_backend.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    get_spaces_endpoint,
    remove_space_endpoint,
)

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
