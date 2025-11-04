# test_get_doc_access_by_roles.py
import allure
import pytest

from tests.test_backend.data.endpoints.Document.document_endpoints import (
    get_document_endpoint,
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
def test_get_project_and_space_doc_access_by_roles(
    request, kind, container_fixture, client_fixture, expected_status, create_main_documents, main_space
):
    """
    Проверяем что разные роли могут получить документы из пространства и проекта. Тест параметризован
    для проверки разных типов клиентов и контейнеров документов.
    """
    with allure.step(f'Подготовка тестовых данных для проверки доступа к документу в {kind}'):
        api_client = request.getfixturevalue(client_fixture)
        container_id = request.getfixturevalue(container_fixture)
        role = client_fixture.replace('_client', '')

    allure.dynamic.title(f'Проверка доступа к документу в {kind} для роли {role}')

    creator_roles = {'owner_client': 'owner', 'manager_client': 'manager', 'member_client': 'member'}

    docs = create_main_documents(kind, container_id, creator_roles)

    with allure.step(f'Проверка доступа к документам ролью {role}'):
        for doc in docs:
            with allure.step(f'Проверка доступа к документу "{doc["title"]}" (создан {doc["creator_role"]})'):
                get_resp = api_client.post(**get_document_endpoint(space_id=main_space, document_id=doc['id']))

                assert get_resp.status_code == expected_status, (
                    f'Ошибка при получении документа: '
                    f'ожидался статус {expected_status}, получили {get_resp.status_code}'
                )

                if get_resp.status_code == 200:
                    doc_data = get_resp.json()['payload']['document']
                    assert doc_data['_id'] == doc['id'], 'Получен неверный документ'
                    assert doc_data['title'] == doc['title'], 'Неверное название документа'


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 403),  # владелец не может получить чужой personal doc
        ('manager_client', 403),  # менеджер не может получить чужой personal doc
        ('member_client', 200),  # участник может получить свой personal doc
        ('guest_client', 403),  # гость не может получить чужой personal doc
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_get_personal_doc_access_by_roles(
    request, client_fixture, expected_status, main_space, main_personal, create_main_documents
):
    """Проверяем что пользователи могут получить только свои personal документы"""
    with allure.step('Подготовка тестовых данных'):
        api_client = request.getfixturevalue(client_fixture)
        role = client_fixture.replace('_client', '')
        member_id = main_personal['member'][0]

    allure.dynamic.title(f'Проверка доступа к personal документу для роли {role}')

    # Создаем документ от имени member
    creator_roles = {'member_client': 'member'}
    docs = create_main_documents('Member', member_id, creator_roles)

    with allure.step(f'Проверка доступа к personal документу ролью {role}'):
        get_resp = api_client.post(**get_document_endpoint(space_id=main_space, document_id=docs[0]['id']))

        assert get_resp.status_code == expected_status, (
            f'Ошибка при получении документа: ' f'ожидался статус {expected_status}, получили {get_resp.status_code}'
        )

        if get_resp.status_code == 200:
            doc_data = get_resp.json()['payload']['document']
            assert doc_data['_id'] == docs[0]['id'], 'Получен неверный документ'
            assert doc_data['title'] == docs[0]['title'], 'Неверное название документа'
