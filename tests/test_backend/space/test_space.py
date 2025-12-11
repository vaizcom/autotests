import allure

from tests.config.generators import generate_space_name
from tests.test_backend.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    get_space_endpoint,
    get_spaces_endpoint,
    edit_space_endpoint,
    remove_space_endpoint,
)

MAX_SPACE_NAME_LENGTH = 30
import pytest

pytestmark = [pytest.mark.backend]


@allure.title('Test create space visible in list')
def test_create_space_visible_in_list(owner_client, temp_space):
    with allure.step('Create space'):
        space_id = temp_space
    with allure.step('Get all spaces'):
        response = owner_client.post(**get_spaces_endpoint())
        assert response.status_code == 200
    with allure.step('Verify created space is in the list'):
        spaces = response.json()['payload']['spaces']
        assert any((s['_id'] == space_id for s in spaces)), f'Space {space_id} not found in list'

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


@allure.title('remove space success')
def remove_space_success(owner_client):  # userId закрыт под Feature Toggle
    name = generate_space_name()
    with allure.step('Create space'):
        create_response = owner_client.post(**create_space_endpoint(name=name))
        assert create_response.status_code == 200
        space_id = create_response.json()['payload']['space']['_id']
    with allure.step('Remove space'):
        remove_response = owner_client.post(**remove_space_endpoint(space_id=space_id))
        assert remove_response.status_code == 200
        assert remove_response.json()['payload']['success']
    with allure.step('Ensure space is no longer in list'):
        list_response = owner_client.post(**get_spaces_endpoint())
        assert all(
            (s['_id'] != space_id for s in list_response.json()['payload']['spaces'])
        ), f'Removed space {space_id} всё ещё найден в GetSpaces'
    with allure.step('Ensure GetSpace returns error for deleted space'):
        get_response = owner_client.post(**get_space_endpoint(space_id=space_id))
        assert get_response.status_code != 200, 'GetSpace по удалённому space вернул 200'


def del_all_spaces(owner_client):
    response = owner_client.post(**get_spaces_endpoint())
    spaces = response.json()['payload']['spaces']

    ids_to_keep = ["6866309d85fb8d104544a61e", "691adf9e4bfde6405d9feb3a"]

    for space in spaces:
        if space['_id'] not in ids_to_keep:
            owner_client.post(**remove_space_endpoint(space_id=space['_id']))