import allure
import pytest

from test_backend.data.endpoints.Space.space_endpoints import get_spaces_endpoint

pytestmark = [pytest.mark.backend]


@allure.title('Test create space visible in list. Создается спейс в котором роль owner')
def test_create_space_visible_in_list(owner_client, temp_space):
    with allure.step('Create space'):
        space_id = temp_space
    with allure.step('Get all spaces'):
        response = owner_client.post(**get_spaces_endpoint())
        assert response.status_code == 200
    with allure.step('Verify created space is in the list'):
        spaces = response.json()['payload']['spaces']
        assert any((s['_id'] == space_id for s in spaces)), f'Space {space_id} not found in list'