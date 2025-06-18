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


MAX_DOC_NAME_LENGTH = 2048


@pytest.mark.parametrize(
    'title, expected_status, expected_actual_title',
    [
        (None, 200, 'Untitled document'),
        ('', 400, None),
        (' ', 200, ' '),
        ('A' * MAX_DOC_NAME_LENGTH, 200, 'A' * MAX_DOC_NAME_LENGTH),
        ('A' * (MAX_DOC_NAME_LENGTH + 1), 400, None),
        # Дополнительно:
        (123, 400, None),
        (True, 400, None),
        ([], 400, None),
        ('Документ', 200, 'Документ'),
        ('😊📄✨', 200, '😊📄✨'),
        ('<script>alert(1)</script>', 200, '<script>alert(1)</script>'),
        ('Title with & < > " \'', 200, 'Title with & < > " \''),
    ],
    ids=[
        'None',
        'empty string',
        'single space',
        'title = MAX length (2048)',
        'title > MAX length (2049)',
        'int as title',
        'bool as title',
        'list as title',
        'cyrillic',
        'emoji',
        'html injection',
        'special chars',
    ],
)
@allure.title('Создание документа с различными значениями title — ожидаемый статус {expected_status}')
def test_document_title_validation(
    owner_client, temp_space, temp_project, title, expected_status, expected_actual_title, request
):
    allure.dynamic.title(f'Создание документа — кейс: [{request.node.callspec.id}] (ожидается {expected_status})')

    with allure.step(f'Отправка запроса [{request.node.callspec.id}] (ожидается {expected_status})'):
        response = owner_client.post(
            **create_document_endpoint(kind='Project', kind_id=temp_project, space_id=temp_space, title=title)
        )

    with allure.step(f'Проверка, что статус ответа = {expected_status}'):
        assert response.status_code == expected_status

    if expected_status == 200:
        with allure.step('Проверка содержимого поля title в payload'):
            document = response.json()['payload']['document']
            assert document['_id']
            actual_title = document.get('title')
            assert actual_title == expected_actual_title


@allure.title('Создание дочерних документов, Проверка status_code и title')
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
