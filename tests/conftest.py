import pytest
from config import settings
from config.generators import generate_space_name, generate_project_name, generate_slug, generate_board_name
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from tests.core.client import APIClient
from tests.core.auth import get_token
from tests.config.settings import API_URL
from tests.test_backend.data.endpoints.Board.constants import DEFAULT_BOARD_GROUPS
from tests.test_backend.data.endpoints.Project.project_endpoints import create_project_endpoint, create_board_endpoint
from tests.test_backend.data.endpoints.Space.space_endpoints import create_space_endpoint, remove_space_endpoint


def pytest_configure(config):
    print(f'\n🧪 Running on stand: {settings.TEST_STAND_NAME}')
    print(f'🔗 API URL: {settings.API_URL}\n')


@pytest.fixture(scope='session')
def guest_client():
    return APIClient(base_url=API_URL, token=get_token('guest'))


@pytest.fixture(scope='session')
def member_client():
    return APIClient(base_url=API_URL, token=get_token('member'))


@pytest.fixture(scope='session')
def manager_client():
    return APIClient(base_url=API_URL, token=get_token('manager'))


# Фикстура: возвращает авторизованного API клиента с токеном владельца
@pytest.fixture(scope='session')
def owner_client():
    return APIClient(base_url=API_URL, token=get_token('owner'))


@pytest.fixture(scope='session')
def foreign_client():
    return APIClient(base_url=API_URL, token=get_token('guest'))


# Фикстура: создает временный спейс и возвращает member_id после прохождения тестов удаляет этот временный спейс
@pytest.fixture(scope='session')
def temp_member(owner_client, temp_space):
    response = owner_client.post(**get_space_members_endpoint(space_id=temp_space))
    response.raise_for_status()

    data = response.json()['payload']
    member_id = data['members'][0]['_id']

    yield member_id


# Фикстура: создает временный спейс и после прохождения тестов удаляет этот временный спейс
@pytest.fixture(scope='session')
def temp_space(owner_client):
    client = owner_client
    name = generate_space_name()
    response = client.post(**create_space_endpoint(name=name))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope='session')
def foreign_space(guest_client):
    """Создаёт space от имени другого пользователя"""
    response = guest_client.post(**create_space_endpoint(name='foreign space'))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    # Очистка
    guest_client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope='module')
def space_id_module(owner_client):
    response = owner_client.post(**create_space_endpoint(name='isolated space'))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    # Удаление после теста
    response = owner_client.post(**remove_space_endpoint(space_id=space_id))
    assert response.status_code == 200


@pytest.fixture(scope='module')
def project_id_module(owner_client, space_id_module):
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'temporary project', 'space_id': space_id_module}
    response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 200
    return response.json()['payload']['project']['_id']


@pytest.fixture(scope='module')
def member_id_module(owner_client, space_id_module):
    response = owner_client.post(**get_space_members_endpoint(space_id=space_id_module))

    data = response.json()['payload']
    member_id = data['members'][0]['_id']

    yield member_id


@pytest.fixture(scope='session')
def temp_project(owner_client, temp_space):
    """Создаёт проект, который используется во всех тестах модуля."""
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'temporary project', 'space_id': temp_space}
    response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 200
    yield response.json()['payload']['project']['_id']


@pytest.fixture(scope='session')
def temp_board(owner_client, temp_project, temp_space):
    """
    Создаёт временную борду в указанном проекте и спейсе.
    """
    board_name = generate_board_name()
    payload = create_board_endpoint(
        name=board_name,
        temp_project=temp_project,
        space_id=temp_space,
        groups=DEFAULT_BOARD_GROUPS,
        typesList=[],
        customFields=[],
    )
    response = owner_client.post(**payload)
    assert response.status_code == 200

    yield response.json()['payload']['board']['_id']
