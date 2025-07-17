import allure
import pytest
from datetime import datetime

from test_backend.data.endpoints.Document.document_endpoints import (
    get_recent_documents_endpoint,
    create_document_endpoint,
    archive_document_endpoint, mark_recent_document_endpoint,
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
    ids=['owner', 'manager', 'member', 'guest']
)
@pytest.mark.parametrize(
    'kind, container_fixture',
    [
        ('Space', 'main_space'),
        ('Project', 'main_project'),
    ],
    ids=['space_docs', 'project_docs'],
)
def test_get_recent_documents_access_by_roles(request, main_space, client_fixture, expected_status,
                                            create_main_documents, kind, container_fixture):
    """
    Проверяем доступ к списку недавних документов для ролей owner, manager, member, guest.
    Тест создаёт тестовые документы, помечает их как недавние и проверяет, что они появляются
    в ответе API для недавних документов в зависимости от роли и ожидаемого статуса.
    """
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    container_id = request.getfixturevalue(container_fixture)

    allure.dynamic.title(f'Получение списка недавних документов ролью {role}')

    creator_roles = {'owner_client': 'owner', 'manager_client': 'manager', 'member_client': 'member'}

    with allure.step('Создание тестовых документов разных типов'):
        created_docs = create_main_documents(kind, container_id, creator_roles)
        assert created_docs, 'Не удалось создать тестовые документы'

        # Маркируем созданные документы как недавние
        with allure.step('Маркировка документов как недавних'):
            for doc in created_docs:
                mark_resp = api_client.post(
                    **mark_recent_document_endpoint(document_id=doc['id'], space_id=main_space)
                )
                assert mark_resp.status_code == 200, (
                    f'Не удалось пометить документ {doc["id"]} как недавний: '
                    f'статус {mark_resp.status_code}'
                )

    created_doc_ids = {doc['id'] for doc in created_docs}

    with allure.step(f'Получение списка недавних документов ролью {role}'):
        recent_resp = api_client.post(**get_recent_documents_endpoint(space_id=main_space))
        assert recent_resp.status_code == expected_status

        if expected_status == 200:
            recent_docs = recent_resp.json()['payload']['recentDocuments']

            with allure.step('Проверка структуры и содержимого ответа'):
                assert isinstance(recent_docs, list), 'recentDocuments должен быть списком'
                assert recent_docs, 'Список недавних документов не должен быть пустым'

                recent_doc_ids = {doc['_id'] for doc in recent_docs}
                missing_docs = created_doc_ids - recent_doc_ids

                assert not missing_docs, (
                    f'Не все документы найдены в списке недавних. '
                    f'Отсутствуют документы с ID: {missing_docs}'
                )

                required_fields = {'_id', 'title', 'kind'}
                for doc in recent_docs:
                    missing_fields = required_fields - doc.keys()
                    assert not missing_fields, f'Отсутствуют обязательные поля: {missing_fields}'


def test_get_recent_documents_empty_space(owner_client, temp_space):
    """Проверяет получение пустого списка недавних документов в пустом пространстве"""

    with allure.step('Запрос списка недавних документов в пустом пространстве'):
        recent_resp = owner_client.post(**get_recent_documents_endpoint(space_id=temp_space))

        assert recent_resp.status_code == 200
        recent_docs = recent_resp.json()['payload']['recentDocuments']
        assert isinstance(recent_docs, list), 'recentDocuments должен быть списком'
        assert len(recent_docs) == 0, 'Список документов должен быть пустым'


def test_get_recent_documents_ordering(owner_client, main_space, main_project):
    """Проверяет сортировку документов в списке недавних (по дате создания, от новых к старым)"""

    doc_ids = []
    try:
        with allure.step('Создание документов с паузой между созданием'):
            for i in range(3):
                title = f'Doc {i} - {datetime.now().strftime("%H:%M:%S.%f")}'
                create_resp = owner_client.post(
                    **create_document_endpoint(
                        kind='Project',
                        kind_id=main_project,
                        space_id=main_space,
                        title=title
                    )
                )
                assert create_resp.status_code == 200
                doc_ids.append(create_resp.json()['payload']['document']['_id'])

        with allure.step('Получение и проверка списка недавних документов'):
            recent_resp = owner_client.post(**get_recent_documents_endpoint(space_id=main_space))
            assert recent_resp.status_code == 200

            recent_docs = recent_resp.json()['payload']['recentDocuments']
            recent_doc_ids = [doc['_id'] for doc in recent_docs[:3]]  # Берем первые 3 документа

            # Проверяем что порядок обратный (от новых к старым)
            assert recent_doc_ids == doc_ids[::-1], 'Неверный порядок документов'

    finally:
        with allure.step('Архивация созданных документов'):
            for doc_id in doc_ids:
                archive_resp = owner_client.post(
                    **archive_document_endpoint(space_id=main_space, document_id=doc_id)
                )
                assert archive_resp.status_code == 200


def test_get_recent_documents_foreign_space_access_denied(foreign_client, space_id_module):
    """Проверяет запрет доступа к списку недавних документов через чужое пространство"""

    with allure.step('Попытка получения недавних документов в чужом пространстве'):
        recent_resp = foreign_client.post(**get_recent_documents_endpoint(space_id=space_id_module))

        assert recent_resp.status_code == 403
        error = recent_resp.json().get('error', {})
        assert error.get('code') == 'AccessDenied'