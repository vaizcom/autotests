import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import get_documents_endpoint

pytestmark = [pytest.mark.backend]


@allure.title('Ошибка при запросе документов с некорректным kind')
def test_get_documents_with_wrong_kind(owner_client, temp_space, temp_project):
    with allure.step('Отправка запроса с несуществующим kind'):
        response = owner_client.post(
            **get_documents_endpoint(kind='WrongKind', kind_id=temp_project, space_id=temp_space)
        )

    with allure.step('Ожидаем 400 ошибку валидации, codes: InvalidForm'):
        assert response.status_code == 400
        assert response.json()['error']['code'] == 'InvalidForm'
