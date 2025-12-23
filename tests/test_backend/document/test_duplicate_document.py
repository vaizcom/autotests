import pytest
import allure
from tests.test_backend.data.endpoints.Document.document_endpoints import (
    duplicate_document_endpoint,
    archive_document_endpoint,
)

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Document Service")
@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_create_and_duplicate_document(owner_client, request, kind, kind_id_fixture, temp_document):
    space_id = request.getfixturevalue('temp_space')

    # Дублируем
    response = owner_client.post(**duplicate_document_endpoint(document_id=temp_document['_id'], space_id=space_id))

    allure.dynamic.title(f'Duplicate document: Создание и дублирование документа ({kind})')

    with allure.step('Проверка успешного дублирования'):
        assert response.status_code == 200
        body = response.json()
        assert body.get('type') == 'DuplicateDocument'
        duplicated = response.json()['payload']['document']
        assert duplicated['_id'] != temp_document['_id']
        assert duplicated['title'] == temp_document['title'] + ' (copy)'
        assert duplicated['kind'] == temp_document['kind']
        assert duplicated['kindId'] == temp_document['kindId']
        assert duplicated.get('map') == temp_document.get('map')

    # Архивируем
    archive = owner_client.post(**archive_document_endpoint(document_id=duplicated['_id'], space_id=space_id))
    assert archive.status_code == 200


@allure.parent_suite("Document Service")
@pytest.mark.parametrize(
    'fake_id, expected_status',
    [
        ('000000000000000000000000', 400),
        ('', 400),
        (None, 400),
        ('bad_format', 400),
    ],
    ids=['not_found', 'empty', 'null', 'bad_format'],
)
def test_duplicate_document_invalid_id(owner_client, space_id_function, fake_id, expected_status):
    allure.dynamic.title(f'Duplicate document Validation: Негативный сценарий- дублирование с некорректным documentId, invalid id={fake_id}')
    with allure.step('Попытка дублирования с invalid id'):
        resp = owner_client.post(
            **duplicate_document_endpoint(
                document_id=fake_id,
                space_id=space_id_function,
            )
        )
        assert resp.status_code == expected_status
        body = resp.json()
        payload = body.get('payload')
        if payload:
            assert 'document' not in payload
        else:
            assert payload is None