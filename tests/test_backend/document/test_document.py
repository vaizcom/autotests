import pytest

from test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint
import allure


pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize('kind', ['Space', 'Project', 'Member'])
def test_create_document(owner_client, temp_space, temp_project, temp_member, kind):
    kind_id_map = {
        'Space': temp_space,
        'Project': temp_project,
        'Member': temp_member,
    }

    kind_id = kind_id_map[kind]
    title = f'Document for {kind}'

    allure.dynamic.title(f'Создание документа: {kind}')

    with allure.step(f'POST /CreateDocument для {kind}'):
        response = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title=title)
        )

    assert response.status_code == 200
    payload = response.json()['payload']
    assert payload['document']['title'] == title
