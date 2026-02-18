import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint
from tests.test_backend.data.endpoints.Document.document_endpoints import (
    archive_document_endpoint,
    get_documents_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.fixture(scope='session')
def excluded_documents(main_space_doc, main_project_doc):
    """
    Возвращает множество исключаемых документов.
    """
    return {main_space_doc, main_project_doc}


@allure.parent_suite("Document Service")
@pytest.mark.parametrize(
    'kind, container_fixture',
    [
        ('Space', 'main_space'),
        ('Project', 'main_project'),
    ],
    ids=['space_docs', 'project_docs'],
)
def test_archive_all_documents(request, owner_client, kind, container_fixture, main_space, excluded_documents):
    """
    Проверяем архивирование всех документов в пространстве и проекте.
    """
    allure.dynamic.title(f"Document Service: Проверяем архивирование всех документов в {kind}")

    with allure.step(f'Подготовка к удалению документов в {kind}'):
        container_id = request.getfixturevalue(container_fixture)

    with allure.step(f'Получение списка документов в {kind}'):
        docs_resp = owner_client.post(**get_documents_endpoint(space_id=main_space, kind=kind, kind_id=container_id))
        assert docs_resp.status_code == 200, 'Не удалось получить список документов'
        # Получаем список ID документов
        doc_ids = [doc['_id'] for doc in docs_resp.json()['payload']['documents']]

    with allure.step(f'Архивирование всех документов в {kind}, кроме исключений'):
        for doc_id in doc_ids:
            if doc_id in excluded_documents:
                allure.step(f'Пропуск документа {doc_id}, т.к. он в списке исключений.')
                continue
            archive_resp = owner_client.post(**archive_document_endpoint(document_id=doc_id, space_id=main_space))
            assert archive_resp.status_code == 200, (
                f'Не удалось архивировать документ {doc_id}: ' f'статус {archive_resp.status_code}')


@allure.parent_suite("Document Service")
@pytest.mark.parametrize(
    'client_fixture, member_key',
    [
        ('owner_client', 'owner'),
        ('manager_client', 'manager'),
        ('member_client', 'member'),
        ('guest_client', 'guest'),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_archive_all_personal_documents(request, main_space, main_personal, client_fixture, member_key):
    """
    Проверяет архивирование ВСЕХ персональных документов для конкретной роли, используя kind='Member'.
    """
    allure.dynamic.title(f'Document Service: archive personal {member_key} Documents')

    api_client = request.getfixturevalue(client_fixture)

    # Получаем ID для kind='Member' из фикстуры main_personal
    # Берем первый элемент списка, так как test_archive_personal_doc использовал main_personal['member'][0]
    kind_id = main_personal[member_key][0]

    with allure.step(f"Создание персонального документа пользователем {member_key}"):
        re = api_client.post(**create_document_endpoint(kind="Member", kind_id=kind_id, space_id=main_space, title=f'Test Personal doc for archiving {member_key}'))
        assert re.status_code == 200

    with allure.step(f'Получение списка документов для {member_key} (kind=Member, id={kind_id})'):
        docs_resp = api_client.post(**get_documents_endpoint(
            space_id=main_space,
            kind='Member',
            kind_id=kind_id
        ))
        assert docs_resp.status_code == 200, 'Не удалось получить список документов'

        documents = docs_resp.json().get('payload', {}).get('documents', [])
        doc_ids = [doc['_id'] for doc in documents]

    if not doc_ids:
        allure.dynamic.description(f"Список документов пуст для {member_key}, архивация не требуется.")
        return

    with allure.step(f'Архивирование {len(doc_ids)} документов клиентом {client_fixture}'):
        for doc_id in doc_ids:
            with allure.step(f'Архивирование документа {doc_id}'):
                archive_resp = api_client.post(**archive_document_endpoint(
                    space_id=main_space,
                    document_id=doc_id
                ))

                # Логируем ошибку, но не обязательно падать, если хотим попробовать удалить остальные
                assert archive_resp.status_code == 200, \
                    f'Не удалось архивировать документ {doc_id}. Статус: {archive_resp.status_code}'

    with allure.step('Post-condition: Проверка, что список документов пуст'):
        docs_resp_after = api_client.post(**get_documents_endpoint(
            space_id=main_space,
            kind='Member',
            kind_id=kind_id
        ))
        assert docs_resp_after.status_code == 200

        remaining = docs_resp_after.json().get('payload', {}).get('documents', [])
        assert len(remaining) == 0, f"Остались неархивированные документы: {len(remaining)}"