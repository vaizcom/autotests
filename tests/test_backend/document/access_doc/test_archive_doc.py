from datetime import datetime
import random

import allure
import pytest

from conftest import member_client
from test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint, archive_document_endpoint,
)

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
def test_archive_space_doc(request, main_space, client_fixture, expected_status):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%d.%m_%H:%M:%S')
    title = f"{current_date}_{role}_Space Doc For List Check"

    allure.dynamic.title(f'Архивирование Space-документа для роли {role}')

    selected_client_name = random.choice(['owner_client', 'manager_client', 'member_client'])
    random_client = request.getfixturevalue(selected_client_name)

    with allure.step(f"random_client({selected_client_name}) создаёт Space-документ для архивации (title = {title})"):
        create_resp = random_client.post(
            **create_document_endpoint(
                kind='Space',
                kind_id=main_space,
                space_id=main_space,
                title=title
            )
        )

        if create_resp.status_code != 200:
            with allure.step(
                    f"Не удалось создать документ, статус {create_resp.status_code} — пропуск проверки списка"):
                assert expected_status == 403
            return

        doc_id = create_resp.json()['payload']['document']['_id']
        with allure.step(f'Архивация Space-документа {title}'):
            archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
            assert archive_resp.status_code == expected_status


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
def test_archive_project_doc(request, main_project, main_space, client_fixture, expected_status):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%d.%m_%H:%M:%S')
    title = f"{current_date}_{role} Project Doc For archive Check"

    allure.dynamic.title(f'Архивирование Project-документа для роли {role}')
    selected_client_name = random.choice(['owner_client', 'manager_client', 'member_client'])

    random_client = request.getfixturevalue(selected_client_name)

    with allure.step(f"random_client({selected_client_name}) создаёт Project-документ для архивации(title:{title})"):
        create_resp = random_client.post(
            **create_document_endpoint(
                kind='Project',
                kind_id=main_project,
                space_id=main_space,
                title=title
            )
        )

        if create_resp.status_code != 200:
            with allure.step(
                    f"Не удалось создать документ, статус {create_resp.status_code} — пропуск проверки списка"):
                assert expected_status == 403
            return

        doc_id = create_resp.json()['payload']['document']['_id']
        with allure.step(f'Архивация Project-документа {title} в роли {role}, {expected_status}'):
            archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
            assert archive_resp.status_code == expected_status

@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 403),
        ('manager_client', 403),
        ('member_client', 200),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_archive_personal_doc(request, main_personal, main_space, client_fixture, expected_status, member_client):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    personal_id = main_personal['member'][0]
    current_date = datetime.now().strftime('%d.%m_%H:%M:%S')
    title = f"{current_date}_{role} Personal Doc For archive Check"

    allure.dynamic.title(f'Архивирование Personal-документа для роли {role}, документ создан в роли Member')

    with allure.step(f"member_client создаёт Personal-документ для архивации ({title})"):
        create_resp = member_client.post(
            **create_document_endpoint(
                kind='Member',
                kind_id=personal_id,
                space_id=main_space,
                title=title
            )
        )

        assert create_resp.status_code == 200

        doc_id = create_resp.json()['payload']['document']['_id']
        with allure.step(f'Архивация Personal-документа в роли {role}, {expected_status}'):
            archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
            assert archive_resp.status_code == expected_status