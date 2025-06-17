import pytest

from test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint
import allure


pytestmark = [pytest.mark.backend]


@allure.title('Создание документа с валидными параметрами')
def test_create_document(owner_client, temp_space, temp_project):
    kind = 'Project'
    kind_id = temp_project  # ID проекта (или другой сущности по kind)
    title = 'Test Document'

    with allure.step('Отправка запроса на создание документа'):
        response = owner_client.post(
            **create_document_endpoint(
                kind=kind,
                kind_id=kind_id,
                space_id=temp_space,
                title=title
            )
        )

    with allure.step('Проверка успешного ответа'):
        assert response.status_code == 200
        response_json = response.json()
        assert 'payload' in response_json
        assert response_json['payload']['document']['title'] == title
