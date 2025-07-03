import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import create_document_endpoint

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('main_client', 200),  # owner of space
        ('manager_client', 200),  # manager in space
        ('member_client', 200),  # member in space
        ('guest_client', 403),  # guest (no membership)
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_create_document_access_by_roles(request, main_space, client_fixture, expected_status):
    """
    Проверка доступа к созданию документа в пространстве main_space для разных ролей.
    owner, manager, member должны успешно создать (200), гость — Forbidden (403).
    """
    space_id = main_space
    api_client = request.getfixturevalue(client_fixture)

    with allure.step(f'{client_fixture} пытается создать документ в space {space_id}'):
        resp = api_client.post(
            **create_document_endpoint(kind='Space', kind_id=space_id, space_id=space_id, title='AccessTestDocument')
        )
        assert (
            resp.status_code == expected_status
        ), f'{client_fixture} ожидает {expected_status}, получен {resp.status_code}'
