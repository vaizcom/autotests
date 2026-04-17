import pytest

from config.generators import generate_space_name
from test_backend.data.endpoints.Space.space_endpoints import create_space_endpoint, remove_space_endpoint


@pytest.fixture(scope="session")
def space_for_history(main_client):
    """
    Создаёт чистый space для проверки history-событий.
    Возвращает dict с space_id и начальным именем.
    Один space на все тесты папки space_events, удаляется после завершения сессии.
    """
    name = generate_space_name()
    resp = main_client.post(**create_space_endpoint(name=name))
    assert resp.status_code == 200, f"Ошибка создания space: {resp.text}"
    space_id = resp.json()['payload']['space']['_id']

    yield {"space_id": space_id, "name": name}

    main_client.post(**remove_space_endpoint(space_id=space_id))
