import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import (
    get_document_endpoint,
    create_document_endpoint,
    archive_document_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 200),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
@pytest.mark.parametrize(
    'kind, container_fixture',
    [
        ('Space', 'main_space'),
        ('Project', 'main_project'),
    ],
    ids=['space_doc', 'project_doc'],
)
def test_get_project_and_space_doc_access_by_roles(request, kind, container_fixture, client_fixture, expected_status):
    """Проверяем что разные роли могут получить доступ к документу из пространства и проекта"""
    with allure.step(f'Подготовка тестовых данных для проверки доступа к документу в {kind}'):
        api_client = request.getfixturevalue(client_fixture)
        container_id = request.getfixturevalue(container_fixture)
        space_id = request.getfixturevalue('main_space')
        role = client_fixture.replace('_client', '')

    allure.dynamic.title(f'Проверка доступа к документу в {kind} для роли {role}')
    created_docs = []

    try:
        with allure.step(f'Создание тестовых документов в {kind} разными ролями'):
            creator_roles = {'owner_client': 'owner', 'manager_client': 'manager', 'member_client': 'member'}

            for creator_fixture, creator_role in creator_roles.items():
                creator_client = request.getfixturevalue(creator_fixture)

                with allure.step(f'Создание документа пользователем {creator_role}'):
                    title = f'{kind} doc by {creator_role}'
                    create_resp = creator_client.post(
                        **create_document_endpoint(kind=kind, kind_id=container_id, space_id=space_id, title=title)
                    )
                    assert create_resp.status_code == 200, (
                        f'Ошибка при создании документа пользователем {creator_role}: '
                        f'статус {create_resp.status_code}'
                    )

                    doc_id = create_resp.json()['payload']['document']['_id']
                    created_docs.append(
                        {'id': doc_id, 'title': title, 'creator': creator_client, 'creator_role': creator_role}
                    )

        with allure.step(f'Проверка доступа к документам ролью {role}'):
            for doc in created_docs:
                with allure.step(f'Проверка доступа к документу "{doc["title"]}" (создан {doc["creator_role"]})'):
                    get_resp = api_client.post(
                        **get_document_endpoint(space_id=space_id, document_id=doc['id'])
                    )

                    assert get_resp.status_code == expected_status, (
                        f'Ошибка при получении документа: '
                        f'ожидался статус {expected_status}, получили {get_resp.status_code}'
                    )

                    if get_resp.status_code == 200:
                        doc_data = get_resp.json()['payload']['document']
                        assert doc_data['_id'] == doc['id'], 'Получен неверный документ'
                        assert doc_data['title'] == doc['title'], 'Неверное название документа'

    finally:
        with allure.step('Очистка тестовых данных'):
            for doc in created_docs:
                with allure.step(f'Удаление документа "{doc["title"]}" (создан {doc["creator_role"]})'):
                    doc['creator'].post(**archive_document_endpoint(space_id=space_id, document_id=doc['id']))


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 403),    # владелец не может получить чужой personal doc
        ('manager_client', 403),  # менеджер не может получить чужой personal doc
        ('member_client', 200),   # участник может получить свой personal doc
        ('guest_client', 403),    # гость не может получить чужой personal doc
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_get_personal_doc_access_by_roles(request, client_fixture, expected_status, main_space, main_personal, member_client):
    """Проверяем что пользователи могут получить только свои personal документы"""
    with allure.step('Подготовка тестовых данных'):
        api_client = request.getfixturevalue(client_fixture)
        role = client_fixture.replace('_client', '')
        member_id = main_personal['member'][0]

    allure.dynamic.title(f'Проверка доступа к personal документу для роли {role}')
    created_docs = []

    try:
        with allure.step('Создание тестового документа'):
            with allure.step('Создание personal документа пользователем member'):
                title = 'Personal doc by member'
                create_resp = member_client.post(
                    **create_document_endpoint(
                        kind='Member',
                        kind_id=member_id,
                        space_id=main_space,
                        title=title
                    )
                )
                assert create_resp.status_code == 200, (
                    f'Ошибка при создании документа пользователем member: '
                    f'статус {create_resp.status_code}'
                )

                doc_id = create_resp.json()['payload']['document']['_id']
                created_docs.append({
                    'id': doc_id,
                    'title': title,
                    'creator': member_client,
                    'creator_role': 'member'
                })

        with allure.step(f'Проверка доступа к personal документу ролью {role} (пользователи могут получить только свои personal документы)'):
            get_resp = api_client.post(
                **get_document_endpoint(space_id=main_space, document_id=doc_id)
            )

            assert get_resp.status_code == expected_status, (
                f'Ошибка при получении документа: '
                f'ожидался статус {expected_status}, получили {get_resp.status_code}'
            )

            if get_resp.status_code == 200:
                doc_data = get_resp.json()['payload']['document']
                assert doc_data['_id'] == doc_id, 'Получен неверный документ'
                assert doc_data['title'] == title, 'Неверное название документа'

    finally:
        with allure.step('Очистка тестовых данных'):
            for doc in created_docs:
                with allure.step(f'Удаление документа "{doc["title"]}" (создан {doc["creator_role"]})'):
                    doc['creator'].post(
                        **archive_document_endpoint(
                            space_id=main_space,
                            document_id=doc['id']
                        )
                    )