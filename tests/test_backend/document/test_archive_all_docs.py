import allure
import pytest
from test_backend.data.endpoints.Document.document_endpoints import (
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
    Проверяем удаление всех документов в пространстве и проекте.
    """
    with allure.step(f'Подготовка к удалению документов в {kind}'):
        container_id = request.getfixturevalue(container_fixture)

    with allure.step(f'Получение списка документов в {kind}'):
        docs_resp = owner_client.post(**get_documents_endpoint(space_id=main_space, kind=kind, kind_id=container_id))
        assert docs_resp.status_code == 200, 'Не удалось получить список документов'
        # Получаем список ID документов
        doc_ids = [doc['_id'] for doc in docs_resp.json()['payload']['documents']]

    with allure.step(f'Удаление всех документов в {kind}, кроме исключений'):
        for doc_id in doc_ids:
            if doc_id in excluded_documents:
                allure.step(f'Пропуск документа {doc_id}, т.к. он в списке исключений.')
                continue
            archive_resp = owner_client.post(**archive_document_endpoint(document_id=doc_id, space_id=main_space))
            assert archive_resp.status_code == 200, (
                f'Не удалось архивировать документ {doc_id}: ' f'статус {archive_resp.status_code}'
            )
