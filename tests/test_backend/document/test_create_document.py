import pytest

from tests.test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint
import allure


pytestmark = [pytest.mark.backend]

@allure.parent_suite("Document Service")
@pytest.mark.parametrize('kind', ['Space', 'Project', 'Member'])
def test_create_document(main_client, temp_space, temp_project, temp_member, kind):
    kind_id_map = {
        'Space': temp_space,
        'Project': temp_project,
        'Member': temp_member,
    }

    kind_id = kind_id_map[kind]
    title = f'Document for {kind}'

    allure.dynamic.title(f'Create document: Создание документа: {kind}')

    with allure.step(f'POST /CreateDocument для {kind}, Проверка status_code и title'):
        response = main_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title=title)
        )

    assert response.status_code == 200
    payload = response.json()['payload']
    assert payload['document']['title'] == title


MAX_DOC_NAME_LENGTH = 2048

@allure.parent_suite("Document Service")
@pytest.mark.parametrize(
    'title, expected_status, expected_actual_title',
    [
        (None, 200, 'Untitled document'),
        (' ', 200, ' '),
        ('A' * MAX_DOC_NAME_LENGTH, 200, 'A' * MAX_DOC_NAME_LENGTH),
        ('A' * (MAX_DOC_NAME_LENGTH + 1), 400, None),
        # Дополнительно:
        (123, 400, None),
        ('Документ', 200, 'Документ'),
        ('😊📄✨', 200, '😊📄✨'),
        ('<script>alert(1)</script>', 200, '<script>alert(1)</script>'),
    ],
    ids=[
        'None',
        'single space',
        'title = MAX length (2048)',
        'title > MAX length (2049)',
        'int as title',
        'cyrillic',
        'emoji',
        'html injection'
    ],
)
def test_document_title_validation(
    main_client, temp_space, temp_project, title, expected_status, expected_actual_title, request
):
    allure.dynamic.title(f'Create document кейс: [{request.node.callspec.id}] (ожидается {expected_status})')

    with allure.step(f'Отправка запроса [{request.node.callspec.id}] (ожидается {expected_status})'):
        response = main_client.post(
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

    elif response.status_code == 400:
        with allure.step('Проверка ошибки валидации по полю "title"'):
            body = response.json()
            error = body.get('error', {})

            with allure.step('Проверка, что error.code == "InvalidForm"'):
                assert (
                    error.get('code') == 'InvalidForm'
                ), f'Ожидался код "InvalidForm", но получен: {error.get("code")}'

            title_codes = []
            with allure.step('Поиск ошибок по полю "title" в error.fields'):
                for field in error.get('fields', []):
                    if field.get('name') == 'title':
                        title_codes = field.get('codes', [])
                        break
                assert title_codes, 'Поле "title" не найдено в error.fields или отсутствуют коды ошибок'

            with allure.step('Проверка конкретного кода ошибки в зависимости от значения title'):
                if title == '':
                    assert (
                        'title should not be empty' in title_codes
                    ), f'Ожидался код "TitleShouldNotBeEmpty", получены: {title_codes}'
                elif isinstance(title, str) and len(title) > MAX_DOC_NAME_LENGTH:
                    assert (
                        'FieldTooLong' in title_codes
                    ), f'Ожидался код "FieldTooLong" при длине > {MAX_DOC_NAME_LENGTH}, получены: {title_codes}'


@allure.parent_suite("Document Service")
@allure.title('Create document: Создание дочерних документов, Проверка status_code и title')
def test_create_child_document(main_client, temp_space, temp_project):
    with allure.step('1. Создание родительского документа'):
        parent_title = 'Parent Doc'
        parent_resp = main_client.post(
            **create_document_endpoint(kind='Project', kind_id=temp_project, space_id=temp_space, title=parent_title)
        )
        assert parent_resp.status_code == 200
        parent = parent_resp.json()['payload']['document']
        parent_id = parent['_id']

    with allure.step('2. Создание первого дочернего документа (index=0)'):
        first_title = 'Child 1'
        first_resp = main_client.post(
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
        second_resp = main_client.post(
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


@allure.parent_suite("Document Service")
@pytest.mark.parametrize(
    'kind, get_fixture, expected_status',
    [
        ('Project', 'temp_project', 200),
        ('Space', 'temp_space', 200),
        ('Member', 'temp_member', 200),
        ('WrongKind', 'temp_project', 400),
        ('Project', 'nonexistent_id', 400),
    ],
    ids=['project', 'space', 'member', 'wrong kind', 'wrong id'],
)
def test_document_kind_and_id(main_client, temp_space, request, kind, get_fixture, expected_status):
    allure.dynamic.title(
        f'Create document: в роли owner - с передачей kind={kind} и kindId (ожидается {expected_status})'
    )

    kind_id = request.getfixturevalue(get_fixture) if get_fixture != 'nonexistent_id' else 'invalid_id'

    with allure.step(
        f'Создание документа Оунером с передачей kind={kind} и kindId={kind_id}  (ожидается {expected_status})'
    ):
        response = main_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title='Kind Test')
        )

    with allure.step('Проверка статус-кода ответа'):
        assert response.status_code == expected_status


@allure.parent_suite("Document Service")
@allure.title('Create document: Создание документа с дублирующимся title')
def test_document_title_duplicates(main_client, temp_space, temp_project):
    title = 'Duplicate Title'

    with allure.step('Создание первого документа с одинаковым title'):
        resp1 = main_client.post(
            **create_document_endpoint(kind='Project', kind_id=temp_project, space_id=temp_space, title=title)
        )
        assert resp1.status_code == 200

    with allure.step('Создание второго документа с тем же title'):
        resp2 = main_client.post(
            **create_document_endpoint(kind='Project', kind_id=temp_project, space_id=temp_space, title=title)
        )
        assert resp2.status_code == 200, 'Поведение зависит от бизнес-логики: разрешены ли дубликаты'


@allure.parent_suite("Document Service")
@allure.title('Create document: Проверка структуры ответа при создании документа')
def test_document_response_structure(main_client, temp_space, temp_project):
    with allure.step('Создание документа'):
        response = main_client.post(
            **create_document_endpoint(kind='Project', kind_id=temp_project, space_id=temp_space)
        )
        assert response.status_code == 200

    with allure.step('Проверка обязательных полей в ответе'):
        document = response.json()['payload']['document']
        for field in ['_id', 'kind']:
            assert field in document, f'Поле {field} отсутствует в payload'


@allure.parent_suite("Document Service")
@allure.title('Create document: Создание документа без авторизации')
def test_create_document_without_auth(foreign_client, temp_space, temp_project):
    with allure.step('Создание документа гостем'):
        response = foreign_client.post(
            **create_document_endpoint(kind='Project', kind_id=temp_project, space_id=temp_space, title='Guest test')
        )
    with allure.step('Ожидаем 400 Unauthorized, проверяем текст ошибки SpaceIdNotSpecified'):
        assert response.status_code in [400, 403]
        assert response.json()['error']['code'] == 'SpaceIdNotSpecified'


@allure.parent_suite("Document Service")
@allure.title('Create document: Создание документа в чужом space')
def test_create_document_in_foreign_space(main_client, foreign_space, temp_project):
    with allure.step('Попытка создать документ в чужом space'):
        response = main_client.post(
            **create_document_endpoint(
                kind='Project', kind_id=temp_project, space_id=foreign_space, title='Wrong space'
            )
        )
    with allure.step('Ожидаем 400, проверяем текст ошибки SpaceIdNotSpecified'):
        assert response.status_code == 400
        assert response.json()['error']['code'] == 'SpaceIdNotSpecified'
