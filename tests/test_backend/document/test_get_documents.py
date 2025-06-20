import pytest
import allure
import random

from tests.test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint, get_documents_endpoint

pytestmark = [pytest.mark.backend]

@pytest.mark.parametrize(
    'kind, fixture_name',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member']
)

def test_get_documents(owner_client, temp_space, request, kind, fixture_name):
    allure.dynamic.title(f'Получение документов — кейс: kind={kind}')

    kind_id = request.getfixturevalue(fixture_name)
    count = random.randint(1, 5)
    titles = [f'Random doc для kind={kind} #{i}' for i in range(count)]

    with allure.step(f'Создание {count} (Random[1,5]) документов с kind={kind}'):
        for title in titles:
            response = owner_client.post(
                **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title=title)
            )
            assert response.status_code == 200

    with allure.step(f'Получение списка документов по kind={kind}'):
        response = owner_client.post(
            **get_documents_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space)
        )
        assert response.status_code == 200
        docs = response.json()['payload']['documents']

    with allure.step('Проверка, что все созданные документы присутствуют в списке'):
        doc_titles = [doc['title'] for doc in docs]
        for title in titles:
            assert title in doc_titles, f'Документ "{title}" не найден в списке'


@pytest.mark.parametrize(
    'kind, kind_id, space_id, expected_status, case_id',
    [
        ('Project', 'nonexistent-id', 'valid_space_id', 400, 'invalid kindId'),
        ('WrongKind', 'valid_project_id', 'valid_space_id', 400, 'invalid kind'),
        (None, 'valid_project_id', 'valid_space_id', 400, 'missing kind'),
        ('Project', None, 'valid_space_id', 400, 'missing kindId'),
    ],
    ids=['invalid kindId', 'invalid kind', 'missing kind', 'missing kindId']
)
def test_get_documents_invalid_inputs(owner_client, temp_space, temp_project, kind, kind_id, space_id, expected_status, case_id):
    allure.dynamic.title(f'Негативный кейс: {case_id}')

    if kind_id == 'valid_project_id':
        kind_id = temp_project

    with allure.step(f'Отправка запроса и проверка статуса {expected_status}, '):
        response = owner_client.post(
            **get_documents_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space)
        )
        assert response.status_code == expected_status, f'Ожидался статус {expected_status}, но получен {response.status_code}'
        assert response.json()['error']['code'] == 'InvalidForm'
