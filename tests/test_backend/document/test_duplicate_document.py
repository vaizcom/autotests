import pytest
import allure
from test_backend.data.endpoints.Document.document_endpoints import duplicate_document_endpoint


@allure.suite('Документы')
@allure.epic('Дублирование документа')
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

    allure.dynamic.title(f'Создание и дублирование документа ({kind.lower()})')

    with allure.step('Проверка успешного дублирования'):
        assert response.status_code == 200
        duplicated = response.json()['payload']['document']
        assert duplicated['_id'] != temp_document['_id']
        assert duplicated['title'] == temp_document['title'] + ' (copy)'
