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
    ids=['project', 'space', 'member'],
)
def test_get_foreign_space_access_denied(owner_client, request, kind, fixture_name, foreign_space):
    kind_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Запрос документов с kind={kind}, но с чужим spaceId')

    with allure.step(f'Попытка запроса с kindId от {kind}, но с чужим spaceId'):
        response = owner_client.post(**get_documents_endpoint(kind=kind, kind_id=kind_id, space_id=foreign_space))

    with allure.step('Проверка, что доступ запрещён'):
        assert response.status_code == 403, f'Ожидался статус 403, но получен {response.status_code}'
        error = response.json().get('error', {})
        assert (
            error.get('code') == 'AccessDenied'
        ), f"Ожидался код ошибки 'AccessDenied', но получен: {error.get('code')}"