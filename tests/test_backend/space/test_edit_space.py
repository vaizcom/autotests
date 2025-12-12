import allure

from tests.config.generators import generate_space_name
from tests.test_backend.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    get_space_endpoint,
    edit_space_endpoint,
)
MAX_SPACE_NAME_LENGTH = 30
import pytest

pytestmark = [pytest.mark.backend]


@allure.title('Test edit space name')
def test_edit_space_name(owner_client, temp_space):
    client = owner_client
    space_id = temp_space
    new_name = generate_space_name() + '_edit'
    with allure.step('Edit space name'):
        response = client.post(**edit_space_endpoint(name=new_name, space_id=space_id))
        assert response.status_code == 200
    with allure.step('Fetch space and verify new name'):
        response = client.post(**get_space_endpoint(space_id=space_id))
        assert response.status_code == 200
        updated_name = response.json()['payload']['space']['name']
        assert updated_name == new_name


@allure.title('Test space name cannot be empty')
def test_space_name_cannot_be_empty(owner_client):
    client = owner_client
    with allure.step('Try to create space with empty name'):
        response = client.post(**create_space_endpoint(name=''))
        assert response.status_code == 400, 'Should fail if space name is empty'


@allure.title('Test space name length limit')
def test_space_name_length_limit(owner_client):
    client = owner_client
    name = 'a' * (MAX_SPACE_NAME_LENGTH + 1)
    with allure.step('Try to create space with too long name'):
        response = client.post(**create_space_endpoint(name=name))
        assert response.status_code == 400, 'Should fail if space name is too long'

@allure.title('Test edit space name can only owner ')
def test_edit_space_can_only_owner(manager_client, temp_space):
    client = manager_client
    space_id = temp_space
    new_name = generate_space_name() + '_edit'
    with allure.step('Edit space name'):
        response = client.post(**edit_space_endpoint(name=new_name, space_id=space_id))
        assert response.status_code == 400
