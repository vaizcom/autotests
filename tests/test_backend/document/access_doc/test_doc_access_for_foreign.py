import pytest
import allure

from tests.test_backend.data.endpoints.Document.document_endpoints import (
    get_documents_endpoint,
    create_document_endpoint,
    get_document_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'kind, fixture_name',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['foreign project', 'foreign space', 'foreign member'],
)
def test_documents_access_denied_for_foreign_user(foreign_client, request, space_id_module, kind, fixture_name):
    """
    Проверяет запрет доступа к документам для стороннего пользователя при попытке
    получить документы, связанные с определенным типом сущности (например, 'Project',
    'Space' или 'Member'). Тест проверяет, что сторонний клиент получает статус 403
    и код ошибки 'AccessDenied' в ответе.
    """
    kind_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Отказ в доступе к {kind} документам другим пользователем')

    with allure.step(f'Попытка получить документы {kind}, принадлежащие чужому space'):
        response = foreign_client.post(**get_documents_endpoint(kind=kind, kind_id=kind_id, space_id=space_id_module))

    with allure.step('Проверка, что возвращён статус 403 и код ошибки AccessDenied'):
        assert response.status_code == 403, f'Ожидался статус 403, но получен {response.status_code}'
        error = response.json().get('error', {})
        assert error.get('code') == 'AccessDenied', f"Ожидался код 'AccessDenied', но получен: {error.get('code')}"


@pytest.mark.parametrize(
    'kind, fixture_name',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_document_foreign_access_denied_for_foreign_space(
    owner_client, request, temp_space, kind, fixture_name, space_id_module
):
    kind_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Попытка получить документ из чужого space (kind={kind}) — должен вернуться AccessDenied')

    with allure.step('Создание документа в своём пространстве'):
        resp = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title='My doc')
        )
        assert resp.status_code == 200
        document_id = resp.json()['payload']['document']['_id']

    with allure.step('Попытка получить этот документ через другой spaceId'):
        resp = owner_client.post(
            **get_document_endpoint(document_id=document_id, space_id=space_id_module)  # temp_space заменён на kind_id
        )
        assert resp.status_code == 403
        assert resp.json().get('error', {}).get('code') == 'AccessDenied'
