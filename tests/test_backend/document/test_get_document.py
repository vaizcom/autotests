import allure
import pytest

from tests.test_backend.data.endpoints.Document.document_endpoints import get_document_endpoint, create_document_endpoint

pytestmark = [pytest.mark.backend]


@allure.parent_suite("Document Service")
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
    allure.dynamic.title(f'Get document: Успешное получение документа по documentId (kind={kind})')

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

        expected_fields = ['_id', 'title', 'kind', 'kindId', 'creator', 'createdAt', 'updatedAt']
        missing_fields = [field for field in expected_fields if field not in data]
        assert not missing_fields, f'В ответе отсутствуют обязательные поля: {missing_fields}'


@allure.parent_suite("Document Service")
@pytest.mark.parametrize(
    'document_id, expected_status, expected_error_code',
    [
        ('nonexistent_id', 400, 'InvalidForm'),
        (None, 400, 'InvalidForm'),
        ('', 400, 'InvalidForm'),
    ],
    ids=['invalid-id', 'missing-id', 'empty-string'],
)
def test_get_document_invalid_input(owner_client, temp_space, document_id, expected_status, expected_error_code):
    allure.dynamic.title(f'Get document validation: Негативный кейс documentId={document_id}')

    with allure.step('Отправка запроса с некорректным или отсутствующим documentId'):
        payload = {'documentId': document_id} if document_id is not None else {}
        resp = owner_client.post(
            path='/GetDocument',
            json=payload,
            headers={'Content-Type': 'application/json', 'Current-Space-Id': temp_space},
        )
        assert resp.status_code == expected_status
        assert resp.json().get('error', {}).get('code') == expected_error_code


@allure.parent_suite("Document Service")
@pytest.mark.parametrize(
    'kind, fixture_name',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_get_document_multiple_requests(owner_client, request, temp_space, kind, fixture_name):
    kind_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Get document: Повторный запрос одного и того же документа (kind={kind})')

    with allure.step('Создание документа'):
        resp = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title='Repeat test doc')
        )
        assert resp.status_code == 200
        document_id = resp.json()['payload']['document']['_id']

    with allure.step('Первый запрос документа'):
        first = owner_client.post(**get_document_endpoint(document_id=document_id, space_id=temp_space))
        assert first.status_code == 200
        first_doc = first.json()['payload']['document']

    with allure.step('Повторный запрос документа'):
        second = owner_client.post(**get_document_endpoint(document_id=document_id, space_id=temp_space))
        assert second.status_code == 200
        second_doc = second.json()['payload']['document']

    with allure.step('Сравнение содержимого документа в ответах'):
        assert first_doc == second_doc, 'Документ в повторном ответе отличается от первого'