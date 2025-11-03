import allure
import pytest
from tests.test_backend.data.endpoints.Document.document_endpoints import (
    get_recent_documents_endpoint,
    create_document_endpoint,
    archive_document_endpoint,
    mark_recent_document_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.skip('BUG: APP-3037 mark_recent_document не перемещает документ вверх списка recent')
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
def test_get_recent_documents_access_by_roles(
    request, main_space, client_fixture, expected_status, kind, container_fixture
):
    """
    Проверяем доступ к списку недавних документов для ролей owner, manager, member, guest.
    Создаются тестовые документы, проверяется их доступность
    и корректный порядок отображения после повторной маркировки.
    """
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    container_id = request.getfixturevalue(container_fixture)
    EXPECTED_DOCS_COUNT = 9

    allure.dynamic.title(f'Получение списка недавних {kind}-документов ролью {role}')

    created_docs = []

    with allure.step(f'Создание {EXPECTED_DOCS_COUNT} тестовых {kind}-документов'):
        # Создаем по 3 документа от каждой роли
        for creator_role in ['owner', 'manager', 'member']:
            creator = request.getfixturevalue(f'{creator_role}_client')
            for i in range(3):
                title = f'Recent document {i+1} by {creator_role}'
                create_resp = creator.post(
                    **create_document_endpoint(kind=kind, kind_id=container_id, space_id=main_space, title=title)
                )
                assert (
                    create_resp.status_code == 200
                ), f'Ошибка при создании документа: статус {create_resp.status_code}'
                doc_id = create_resp.json()['payload']['document']['_id']
                created_docs.append({'id': doc_id, 'title': title, 'creator': creator, 'creator_role': creator_role})

    try:
        docs_count = len(created_docs)
        assert (
            docs_count == EXPECTED_DOCS_COUNT
        ), f'Неверное количество созданных документов: {docs_count}, ожидалось: {EXPECTED_DOCS_COUNT}'

        with allure.step('Маркировка документов как недавних'):
            for doc in created_docs:
                mark_resp = api_client.post(**mark_recent_document_endpoint(document_id=doc['id'], space_id=main_space))
                assert mark_resp.status_code == 200, (
                    f'Не удалось пометить документ {doc["id"]} как недавний: ' f'статус {mark_resp.status_code}'
                )

        with allure.step(f'Получение списка недавних документов ролью {role}'):
            recent_resp = api_client.post(**get_recent_documents_endpoint(space_id=main_space))
            assert recent_resp.status_code == expected_status

            if expected_status == 200:
                recent_docs = recent_resp.json()['payload']['recentDocuments']

                with allure.step('Проверка структуры и содержимого ответа'):
                    assert isinstance(recent_docs, list), 'recentDocuments должен быть списком'
                    assert recent_docs, 'Список недавних документов не должен быть пустым'
                    received_count = len(recent_docs)
                    assert received_count == EXPECTED_DOCS_COUNT, (
                        f'Неверное количество документов в ответе: {received_count}, '
                        f'ожидалось: {EXPECTED_DOCS_COUNT}'
                    )

                    recent_doc_ids = {doc['_id'] for doc in recent_docs}
                    created_doc_ids = {doc['id'] for doc in created_docs}
                    missing_docs = created_doc_ids - recent_doc_ids
                    assert not missing_docs, (
                        f'Не все документы найдены в списке недавних. ' f'Отсутствуют документы с ID: {missing_docs}'
                    )

                    required_fields = {'_id', 'title', 'kind'}
                    for doc in recent_docs:
                        missing_fields = required_fields - doc.keys()
                        assert not missing_fields, f'Отсутствуют обязательные поля: {missing_fields}'

                    # Проверяем порядок документов только если создано ожидаемое количество
                    if received_count == EXPECTED_DOCS_COUNT:
                        original_ids = [doc['_id'] for doc in recent_docs]

                        with allure.step('Повторная маркировка документов для проверки порядка'):
                            for doc in recent_docs[::-1]:
                                mark_resp = api_client.post(
                                    **mark_recent_document_endpoint(document_id=doc['_id'], space_id=main_space)
                                )
                                assert mark_resp.status_code == 200

                        updated_resp = api_client.post(**get_recent_documents_endpoint(space_id=main_space))
                        updated_docs = updated_resp.json()['payload']['recentDocuments']
                        updated_ids = [doc['_id'] for doc in updated_docs]

                        # TODO: BUG: APP-3037 mark_recent_document_endpoint не перемещает документ на верх списка recent
                        # Когда баг будет исправлен — ожидаем, что порядок изменится на обратный:
                        # assert updated_ids == original_ids[::-1]
                        # Пока баг не исправлен, этот ассерт падает — оставляем для контроля
                        assert (
                            updated_ids == original_ids[::-1]
                        ), 'Порядок документов после повторной маркировки неверный'

    finally:
        with allure.step('Удаление тестовых документов'):
            for doc in created_docs:
                doc['creator'].post(**archive_document_endpoint(space_id=main_space, document_id=doc['id']))
