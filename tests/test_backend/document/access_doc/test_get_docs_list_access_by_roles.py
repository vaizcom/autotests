import allure
import pytest
from test_backend.data.endpoints.Document.document_endpoints import get_documents_endpoint

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
    ids=['space_docs', 'project_docs'],
)
def test_get_project_and_space_docs_access_by_roles(
    request, kind, container_fixture, client_fixture, expected_status, create_main_documents
):
    """Проверяем что разные роли могут получить список документов из пространства и проекта"""
    with allure.step(f'Подготовка тестовых данных для проверки доступа к документам в {kind}'):
        api_client = request.getfixturevalue(client_fixture)
        container_id = request.getfixturevalue(container_fixture)
        space_id = request.getfixturevalue('main_space')
        role = client_fixture.replace('_client', '')

    allure.dynamic.title(f'Проверка доступа к списку документов в {kind} для роли {role}')

    # Создаем документы с помощью фикстуры
    creator_roles = {'owner_client': 'owner', 'manager_client': 'manager', 'member_client': 'member'}
    created_docs = create_main_documents(kind, container_id, creator_roles)

    with allure.step(f'Проверка получения списка документов ролью {role}'):
        list_resp = api_client.post(**get_documents_endpoint(kind=kind, kind_id=container_id, space_id=space_id))

        assert list_resp.status_code == expected_status, (
            f'Ошибка при получении списка документов: '
            f'ожидался статус {expected_status}, получили {list_resp.status_code}'
        )

    if list_resp.status_code == 200:
        with allure.step('Проверка наличия всех созданных документов в списке'):
            docs = list_resp.json()['payload']['documents']
            doc_ids = [doc['_id'] for doc in docs]

            for created_doc in created_docs:
                assert created_doc['id'] in doc_ids, (
                    f'Документ "{created_doc["title"]}" (создан {created_doc["creator_role"]}) ' f'не найден в списке'
                )


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 403),  # владелец не может получить чужие personal docs
        ('manager_client', 403),  # менеджер не может получить чужие personal docs
        ('member_client', 200),  # участник может получить свои personal docs
        ('guest_client', 403),  # гость не может получить чужие personal docs
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_get_personal_docs_access_by_roles(
    request, client_fixture, expected_status, main_space, main_personal, create_main_documents
):
    """Проверяем что пользователи могут получить только свои personal документы"""
    with allure.step('Подготовка тестовых данных'):
        api_client = request.getfixturevalue(client_fixture)
        role = client_fixture.replace('_client', '')
        member_id = main_personal['member'][0]  # Берём ID member для проверки доступа к его документам

    allure.dynamic.title(f'Проверка доступа к personal документам для роли {role}')

    # Создаем документы с помощью фикстуры
    creator_roles = {'member_client': 'member'}
    created_docs = create_main_documents('Member', member_id, creator_roles)

    with allure.step(f'Проверка получения personal документов ролью {role}'):
        list_resp = api_client.post(**get_documents_endpoint(kind='Member', kind_id=member_id, space_id=main_space))

        assert list_resp.status_code == expected_status, (
            f'Ошибка при получении списка документов: '
            f'ожидался статус {expected_status}, получили {list_resp.status_code}'
        )

    if list_resp.status_code == 200:
        with allure.step('Проверка наличия созданного документа в списке'):
            docs = list_resp.json()['payload']['documents']
            doc_ids = [doc['_id'] for doc in docs]

            for created_doc in created_docs:
                assert created_doc['id'] in doc_ids, (
                    f'Документ "{created_doc["title"]}" (создан {created_doc["creator_role"]}) ' f'не найден в списке'
                )
