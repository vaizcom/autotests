import pytest
from backend_tests.core.client import APIClient
from backend_tests.core.auth import get_token
from backend_tests.config.settings import API_URL
from backend_tests.data.endpoints.Project.project_endpoints import create_project_endpoint, create_board_endpoint
from backend_tests.utils.generators import generate_space_name, generate_board_name
from backend_tests.utils.generators import generate_project_name, generate_slug
from backend_tests.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    remove_space_endpoint
)


@pytest.fixture
def guest_client():
    return APIClient(base_url=API_URL, token=get_token("guest"))

@pytest.fixture
def member_client():
    return APIClient(base_url=API_URL, token=get_token("member"))

@pytest.fixture
def manager_client():
    return APIClient(base_url=API_URL, token=get_token("manager"))


# Фикстура: возвращает авторизованного API клиента с токеном владельца
@pytest.fixture(scope="session")
def owner_client():
    token = get_token("owner")
    client = APIClient(base_url=API_URL)
    client.set_auth_header(token)
    return client

# Фикстура: создает временный спейс и после прохождения тестов удаляет этот временный спейс
@pytest.fixture(scope="function")
def temp_space(owner_client):
    client = owner_client
    name = generate_space_name()
    response = client.post(**create_space_endpoint(name=name))
    assert response.status_code == 200
    space_id = response.json()["payload"]["space"]["_id"]

    yield space_id

    client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope='function')
def temp_project(owner_client, temp_space):
    """Создаёт проект, который используется во всех тестах модуля."""
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'temporary project', 'space_id': temp_space}
    response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 200
    return response.json()['payload']['project']['_id']


@pytest.fixture(scope='function')
def temp_board(owner_client, temp_project, temp_space):
    """
    Создаёт временную борду в указанном проекте и пространстве.
    """
    board_name = generate_board_name()
    payload = create_board_endpoint(
        name=board_name,
        temp_project=temp_project,
        space_id=temp_space,
        groups=[],
        typesList=[],
        customFields=[]
    )
    response = owner_client.post(**payload)
    assert response.status_code == 200

    return response.json()["payload"]["board"]["_id"]
