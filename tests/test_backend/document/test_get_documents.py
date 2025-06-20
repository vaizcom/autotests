import pytest
import allure
import random

from tests.test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint, get_documents_endpoint


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
    allure.dynamic.title(f'Получение документов — кейс: [{request.node.callspec.id}] kind={kind}')

    kind_id = request.getfixturevalue(fixture_name)
    count = random.randint(1, 5)
    titles = [f'Random doc для kind={kind} #{i}' for i in range(count)]

    with allure.step(f'Создание {count} документов с kind={kind}'):
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


@allure.title('Ошибка при запросе документов с некорректным kind')
def test_get_documents_with_wrong_kind(owner_client, temp_space, temp_project):
    with allure.step('Отправка запроса с несуществующим kind'):
        response = owner_client.post(
            **get_documents_endpoint(kind='WrongKind', kind_id=temp_project, space_id=temp_space)
        )

    with allure.step('Ожидаем 400 ошибку валидации, codes: InvalidForm'):
        assert response.status_code == 400
        assert response.json()['error']['code'] == 'InvalidForm'
