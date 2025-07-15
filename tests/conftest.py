import pytest
import allure
from config import settings
from config.generators import generate_space_name, generate_project_name, generate_slug, generate_board_name
from test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint, archive_document_endpoint
from test_backend.data.endpoints.member.member_endpoints import get_space_members_endpoint
from tests.core.client import APIClient
from tests.core.auth import get_token
from tests.config.settings import API_URL, MAIN_SPACE_ID
from tests.test_backend.data.endpoints.Board.constants import DEFAULT_BOARD_GROUPS
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    create_project_endpoint,
    create_board_endpoint,
    get_project_endpoint,
)
from tests.test_backend.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    remove_space_endpoint,
    get_space_endpoint,
)
from datetime import datetime


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


@pytest.fixture(scope='session')
def main_client():
    return APIClient(base_url=API_URL, token=get_token('main'))


@pytest.fixture(scope='session')
def main_space(main_client) -> str:
    """
    Отличие этого спейса в том, что в  этом спейсе уже есть мемберы с разными ролями.
    """

    assert MAIN_SPACE_ID, 'Не задана переменная окружения MAIN_SPACE_ID'
    resp = main_client.post(**get_space_endpoint(space_id=MAIN_SPACE_ID))
    assert resp.status_code == 200, f'Space {MAIN_SPACE_ID} not found: {resp.text}'
    return MAIN_SPACE_ID


@pytest.fixture(scope='session')
def main_project(main_client, main_space):
    response = main_client.post(**get_project_endpoint(project_id='686672af85fb8d104544e798', space_id=main_space))
    assert response.status_code == 200
    return response.json()['payload']['project']['_id']


@pytest.fixture(scope='session')
def main_personal(main_client, main_space):
    """Возвращает персональные ID участников пространства по ролям."""
    response = main_client.post(**get_space_members_endpoint(space_id=main_space))
    response.raise_for_status()

    members = response.json()['payload']['members']
    roles = ['owner', 'manager', 'member', 'guest']

    # Собираем _id участников для каждой роли по имени (или другому признаку)
    member_id = {role: [m['_id'] for m in members if m.get('fullName') == role] for role in roles}
    return member_id


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
    client = owner_client
    name = generate_space_name()
    response = client.post(**create_space_endpoint(name=name))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope='module')
def project_id_module(owner_client, space_id_module):
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'temporary project', 'space_id': space_id_module}
    response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 200
    project_id = response.json()['payload']['project']['_id']

    yield project_id


@pytest.fixture(scope='module')
def member_id_module(owner_client, space_id_module):
    response = owner_client.post(**get_space_members_endpoint(space_id=space_id_module))
    response.raise_for_status()

    data = response.json()['payload']
    member_id = data['members'][0]['_id']

    yield member_id


@pytest.fixture(scope='function')
def space_id_function(owner_client):
    client = owner_client
    name = generate_space_name()
    response = client.post(**create_space_endpoint(name=name))
    assert response.status_code == 200
    space_id = response.json()['payload']['space']['_id']

    yield space_id

    client.post(**remove_space_endpoint(space_id=space_id))


@pytest.fixture(scope='function')
def project_id_function(owner_client, space_id_function):
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'temporary project', 'space_id': space_id_function}
    response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 200
    project_id = response.json()['payload']['project']['_id']

    yield project_id


@pytest.fixture(scope='function')
def member_id_function(owner_client, space_id_function):
    response = owner_client.post(**get_space_members_endpoint(space_id=space_id_function))
    response.raise_for_status()

    data = response.json()['payload']
    member_id = data['members'][0]['_id']

    yield member_id


@pytest.fixture
def temp_document(owner_client, request, kind, kind_id_fixture):
    kind_id = request.getfixturevalue(kind_id_fixture)
    space_id = request.getfixturevalue('temp_space')

    response = owner_client.post(
        **create_document_endpoint(
            kind=kind,
            kind_id=kind_id,
            space_id=space_id,
            title='Документ для дублирования',
        )
    )

    assert response.status_code == 200
    doc_id = response.json()['payload']['document']

    yield doc_id

    owner_client.post(**archive_document_endpoint(space_id=space_id, document_id=doc_id))


@pytest.fixture
def create_main_documents(request, main_space):
    """
    Фикстура для создания тестовых документов разными ролями в main_space
    """
    created_docs = []

    def _create_docs(kind, kind_id, creator_roles):
        """
        Внутренняя функция для создания документов
        Args:
            kind (str): Тип документа (Space/Project/Member)
            kind_id (str): ID контейнера (space_id/project_id/member_id)
            creator_roles (dict): Словарь {fixture_name: role_name} для создания документов
        """
        with allure.step(f'Создание тестовых документов в {kind} разными ролями'):
            for creator_fixture, creator_role in creator_roles.items():
                creator_client = request.getfixturevalue(creator_fixture)

                with allure.step(f'Создание документа пользователем {creator_role}'):
                    title = f'{kind} doc by {creator_role} {datetime.now().strftime("%Y.%m.%d_%H:%M:%S")}'
                    create_resp = creator_client.post(
                        **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=main_space, title=title)
                    )
                    assert create_resp.status_code == 200, (
                        f'Ошибка при создании документа пользователем {creator_role}: '
                        f'статус {create_resp.status_code}'
                    )

                    doc_id = create_resp.json()['payload']['document']['_id']
                    created_docs.append(
                        {'id': doc_id, 'title': title, 'creator': creator_client, 'creator_role': creator_role}
                    )
        return created_docs

    yield _create_docs

    # Очистка тестовых данных
    with allure.step('Очистка тестовых данных'):
        for doc in created_docs:
            with allure.step(f'Удаление документа "{doc["title"]}" (создан {doc["creator_role"]})'):
                doc['creator'].post(**archive_document_endpoint(space_id=main_space, document_id=doc['id']))
