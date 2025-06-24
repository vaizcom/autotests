import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import get_document_endpoint, create_document_endpoint

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'kind, fixture_name',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_get_document_success(owner_client, request, temp_space, kind, fixture_name):
    kind_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Успешное получение документа по documentId (kind={kind})')

    with allure.step(f'Создание документа (kind={kind})'):
        resp = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title='test doc')
        )
        assert resp.status_code == 200
        document_id = resp.json()['payload']['document']['_id']

    with allure.step('Запрос документа по его documentId'):
        resp = owner_client.post(**get_document_endpoint(document_id=document_id, space_id=temp_space))
        assert resp.status_code == 200
        data = resp.json().get('payload', {}).get('document')
        assert data is not None, 'Документ не найден в ответе'
        assert data['_id'] == document_id, 'Получен неверный документ'


@pytest.mark.parametrize(
    'document_id, expected_status, expected_error_code',
    [
        ('nonexistent_id', 400, 'InvalidForm'),
        (None, 400, 'InvalidForm'),
        ('', 400, 'InvalidForm'),
        (123, 400, 'InvalidForm'),
        ('abc', 400, 'InvalidForm'),
        ('!@#$', 400, 'InvalidForm'),
        ({'id': '123'}, 400, 'InvalidForm'),
    ],
    ids=['invalid-id', 'missing-id', 'empty-string', 'int-id', 'short-str', 'special-chars', 'json-object'],
)
def test_get_document_invalid_input(owner_client, temp_space, document_id, expected_status, expected_error_code):
    allure.dynamic.title(f'Негативный кейс: documentId={document_id}')

    with allure.step('Отправка запроса с некорректным или отсутствующим documentId'):
        payload = {'documentId': document_id} if document_id is not None else {}
        resp = owner_client.post(
            path='/GetDocument',
            json=payload,
            headers={'Content-Type': 'application/json', 'Current-Space-Id': temp_space},
        )
        assert resp.status_code == expected_status
        assert resp.json().get('error', {}).get('code') == expected_error_code


@pytest.mark.parametrize(
    'kind, fixture_name',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_get_document_foreign_access_denied(owner_client, request, temp_space, foreign_space, kind, fixture_name):
    kind_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Попытка получить документ из чужого space (kind={kind}) — должен вернуться AccessDenied')

    with allure.step('Создание документа в своём пространстве'):
        resp = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title='My doc')
        )
        assert resp.status_code == 200
        document_id = resp.json()['payload']['document']['_id']

    with allure.step('Попытка получить этот документ через чужой spaceId'):
        resp = owner_client.post(
            **get_document_endpoint(document_id=document_id, space_id=foreign_space)
        )
        assert resp.status_code == 403
        assert resp.json().get('error', {}).get('code') == 'AccessDenied'
