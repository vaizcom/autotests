from datetime import datetime

import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    duplicate_document_endpoint,
    archive_document_endpoint,
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
def test_duplicate_space_doc_access_by_roles(request, main_space, client_fixture, expected_status):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} Doc For Duplication'

    allure.dynamic.title(f'Дублирование Space-документа для роли {role}')

    # Создание документа для дублирования
    with allure.step('Создание Space-документа'):
        create_resp = api_client.post(
            **create_document_endpoint(kind='Space', kind_id=main_space, space_id=main_space, title=title)
        )
        if create_resp.status_code != 200:
            with allure.step(f'Не удалось создать документ, статус {create_resp.status_code} — пропуск дублирования'):
                assert (
                    expected_status == 403
                ), f'Невозможно протестировать дублирование без документа (статус создания {create_resp.status_code})'
            return

        doc_id = create_resp.json()['payload']['document']['_id']

        with allure.step(f'{role} пытается продублировать документ'):
            dup_resp = api_client.post(**duplicate_document_endpoint(document_id=doc_id, space_id=main_space))
            if dup_resp.status_code != expected_status:
                allure.attach(dup_resp.text, name='Response Body', attachment_type=allure.attachment_type.JSON)
            assert dup_resp.status_code == expected_status, f'Ожидали {expected_status}, получили {dup_resp.status_code}'

        doc_copy_id = dup_resp.json()['payload']['document']['_id']

    with allure.step('Архивация исходного документа (cleanup)'):
        archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
        assert archive_resp.status_code == 200

    with allure.step('Архивация Copy-документа (cleanup)'):
        archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_copy_id))
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
def test_duplicate_project_doc_access_by_roles(request, main_space, main_project, client_fixture, expected_status):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} Project Doc For Duplication'

    allure.dynamic.title(f'Дублирование Project-документа для роли {role}')

    # Создание документа для дублирования
    with allure.step('Создание Project-документа'):
        create_resp = api_client.post(
            **create_document_endpoint(kind='Project', kind_id=main_project, space_id=main_space, title=title)
        )
        if create_resp.status_code != 200:
            with allure.step(f'Не удалось создать документ, статус {create_resp.status_code} — пропуск дублирования'):
                assert (
                    expected_status == 403
                ), f'Невозможно протестировать дублирование без документа (статус создания {create_resp.status_code})'
            return

        doc_id = create_resp.json()['payload']['document']['_id']

        with allure.step(f'{role} пытается продублировать документ'):
            dup_resp = api_client.post(**duplicate_document_endpoint(document_id=doc_id, space_id=main_space))
            if dup_resp.status_code != expected_status:
                allure.attach(dup_resp.text, name='Response Body', attachment_type=allure.attachment_type.JSON)
            assert dup_resp.status_code == expected_status, f'Ожидали {expected_status}, получили {dup_resp.status_code}'

        if expected_status == 200:
            doc_copy_id = dup_resp.json()['payload']['document']['_id']

    with allure.step('Архивация исходного документа (cleanup)'):
        archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
        assert archive_resp.status_code == 200

    if expected_status == 200:
        with allure.step('Архивация Copy-документа (cleanup)'):
            archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_copy_id))
            assert archive_resp.status_code == 200