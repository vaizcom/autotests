import allure
import pytest
from tests.config.generators import generate_space_name
from tests.test_backend.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    get_space_endpoint,
    get_spaces_endpoint,
    remove_space_endpoint,
)

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Space Service")
@allure.suite("Remove space")
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


@allure.parent_suite("Space Service")
@allure.suite("Remove space")
@allure.title('remove all spaces')
def del_all_spaces(owner_client):
    response = owner_client.post(**get_spaces_endpoint())
    spaces = response.json()['payload']['spaces']

    ids_to_keep = ["6866309d85fb8d104544a61e", "691adf9e4bfde6405d9feb3a"]

    for space in spaces:
        if space['_id'] not in ids_to_keep:
            owner_client.post(**remove_space_endpoint(space_id=space['_id']))