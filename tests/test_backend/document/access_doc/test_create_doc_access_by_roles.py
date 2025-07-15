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
def test_create_and_archive_space_doc_access_by_roles(request, main_space, client_fixture, expected_status):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} {role} Space Doc'

    allure.dynamic.title(f'Создание Space-документа для роли {role}')

    with allure.step(f'{role} создаёт Space-документ, {expected_status}'):
        with resource_lock:
            endpoint_args = create_document_endpoint(
                kind='Space', 
                kind_id=main_space, 
                space_id=main_space, 
                title=title
            )
            resp = api_client.post(**endpoint_args)
            
            if resp.status_code != expected_status:
                print(f"\nRequest failed:")
                print(f"Role: {role}")
                print(f"Space ID: {main_space}")
                print(f"Response status: {resp.status_code}")
                print(f"Response body: {resp.text}")
            
            assert resp.status_code == expected_status

            if expected_status == 200:
                doc_id = resp.json()['payload']['document']['_id']
                with allure.step('Созданный Space-документ содержит title'):
                    assert resp.json()['payload']['document']['title'] == title

                with allure.step('Архивация Space-документа'):
                    archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
                    if archive_resp.status_code != 200:
                        print(f"\nArchive request failed:")
                        print(f"Role: {role}")
                        print(f"Doc ID: {doc_id}")
                        print(f"Response status: {archive_resp.status_code}")
                        print(f"Response body: {archive_resp.text}")
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
def test_create_and_archive_project_doc_access_by_roles(
    request, main_project, main_space, client_fixture, expected_status
):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} Project Doc'

    allure.dynamic.title(f'Создание Project-документа для роли {role}')

    with allure.step(f'{role} создаёт Project-документ, {expected_status}'):
        resp = api_client.post(
            **create_document_endpoint(kind='Project', kind_id=main_project, space_id=main_space, title=title)
        )
        assert resp.status_code == expected_status

        if expected_status == 200:
            with allure.step('Созданный Project-документ содержит title'):
                assert resp.json()['payload']['document']['title'] == title
                doc_id = resp.json()['payload']['document']['_id']
            with allure.step(f'Архивация Project-документа, {expected_status}'):
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
def test_create_and_archive_personal_doc_access_by_roles(
    request, main_personal, client_fixture, expected_status, main_space
):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    personal_id = main_personal[role][0]
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} Personal Doc'

    allure.dynamic.title(f'Создание Personal-документа для роли {role}')

    with allure.step(f'{role} создаёт Personal-документ, {expected_status}'):
        resp = api_client.post(
            **create_document_endpoint(kind='Member', kind_id=personal_id, space_id=main_space, title=title)
        )
        assert resp.status_code == expected_status

    with allure.step('Созданный Personal-документ содержит title'):
        assert resp.json()['payload']['document']['title'] == title

        if expected_status == 200:
            doc_id = resp.json()['payload']['document']['_id']
    with allure.step('Архивация Personal-документа'):
        archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
        assert archive_resp.status_code == 200