import allure
import pytest
from datetime import datetime

from test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint, archive_document_endpoint

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_create_space_doc_access_by_roles(request, main_space, client_fixture, expected_status):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} {role} Space Doc'

    allure.dynamic.title(f'Создание Space-документа для роли {role}')

    with allure.step(f'{role} создаёт Space-документ'):
        resp = api_client.post(
            **create_document_endpoint(
                kind='Space', kind_id=main_space, space_id=main_space, title=title
            )
        )
        assert resp.status_code == expected_status

        if expected_status == 200:
            doc_id = resp.json()['payload']['document']['_id']
            with allure.step(f'Архивация Space-документа {title}'):
                archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
                assert archive_resp.status_code == 200


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_create_project_doc_access_by_roles(request, main_project, main_space, client_fixture, expected_status):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} {role} Project Doc'

    allure.dynamic.title(f'Создание Project-документа для роли {role}')

    with allure.step(f'{role} создаёт Project-документ {title}'):
        resp = api_client.post(
            **create_document_endpoint(
                kind='Project', kind_id=main_project, space_id=main_space, title=title
            )
        )
        assert resp.status_code == expected_status

        if expected_status == 200:
            doc_id = resp.json()['payload']['document']['_id']
            with allure.step(f'Архивация Project-документа {title}'):
                archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
                assert archive_resp.status_code == 200


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 200),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_create_personal_doc_access_by_roles(request, main_personal, client_fixture, expected_status, main_space):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    personal_id = main_personal[role][0]
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} {role} Personal Doc'

    allure.dynamic.title(f'Создание Personal-документа для роли {role}')

    with allure.step(f'{role} создаёт Personal-документ {title}'):
        resp = api_client.post(
            **create_document_endpoint(
                kind='Member', kind_id=personal_id, space_id=main_space, title=title
            )
        )
        assert resp.status_code == expected_status

        if expected_status == 200:
            doc_id = resp.json()['payload']['document']['_id']
            with allure.step(f'Архивация Personal-документа {title}'):
                archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
                assert archive_resp.status_code == 200
