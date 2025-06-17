import pytest

from test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint
import allure


pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize('kind', ['Space', 'Project', 'Member'])
def test_create_document(owner_client, temp_space, temp_project, temp_member, kind):
    kind_id_map = {
        'Space': temp_space,
        'Project': temp_project,
        'Member': temp_member,
    }

    kind_id = kind_id_map[kind]
    title = f'Document for {kind}'

    allure.dynamic.title(f'Создание документа: {kind}')

    with allure.step(f'POST /CreateDocument для {kind}, Проверка status_code и title'):
        response = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title=title)
        )

    assert response.status_code == 200
    payload = response.json()['payload']
    assert payload['document']['title'] == title


@allure.title('Создание дочерних документов')
@allure.title('BUG: APP-2842 CreateDocument не возвращает index и parentDocumentId в ответе')
def test_create_child_document(owner_client, temp_space, temp_project):
    with allure.step('1. Создание родительского документа'):
        parent_title = 'Parent Doc'
        parent_resp = owner_client.post(
            **create_document_endpoint(kind='Project', kind_id=temp_project, space_id=temp_space, title=parent_title)
        )
        assert parent_resp.status_code == 200
        parent = parent_resp.json()['payload']['document']
        parent_id = parent['_id']

    with allure.step('2. Создание первого дочернего документа (index=0)'):
        first_title = 'Child 1'
        first_resp = owner_client.post(
            **create_document_endpoint(
                kind='Project',
                kind_id=temp_project,
                space_id=temp_space,
                parent_document_id=parent_id,
                index=0,
                title=first_title,
            )
        )
        assert first_resp.status_code == 200
        first_doc = first_resp.json()['payload']['document']
        assert first_doc['title'] == first_title

    with allure.step('3. Создание второго дочернего документа (index=1)'):
        second_title = 'Child 2'
        second_resp = owner_client.post(
            **create_document_endpoint(
                kind='Project',
                kind_id=temp_project,
                space_id=temp_space,
                parent_document_id=parent_id,
                index=1,
                title=second_title,
            )
        )
        assert second_resp.status_code == 200
        second_doc = second_resp.json()['payload']['document']
        assert second_doc['title'] == second_title
