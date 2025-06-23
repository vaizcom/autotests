import pytest
import allure

from test_backend.data.endpoints.Document.document_endpoints import get_documents_endpoint

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
    target_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Отказ в доступе к {kind} документам другим пользователем')

    with allure.step(f'Попытка получить документы {kind}, принадлежащие чужому space'):
        response = foreign_client.post(**get_documents_endpoint(kind=kind, kind_id=target_id, space_id=space_id_module))

    with allure.step('Проверка, что возвращён статус 403 и код ошибки AccessDenied'):
        assert response.status_code == 403, f'Ожидался статус 403, но получен {response.status_code}'
        error = response.json().get('error', {})
        assert error.get('code') == 'AccessDenied', f"Ожидался код 'AccessDenied', но получен: {error.get('code')}"
