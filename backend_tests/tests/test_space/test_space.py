import uuid
from backend_tests.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    get_space_endpoint,
    get_spaces_endpoint,
    edit_space_endpoint,
    remove_space_endpoint
)
from backend_tests.utils.generators import generate_space_name, generate_project_name

MAX_SPACE_NAME_LENGTH = 30

# Тест: создаёт space и проверяет наличие в списке
def test_create_space_visible_in_list(owner_client, temp_space):
    client = owner_client
    space_id = temp_space

    response = client.post(**get_spaces_endpoint())
    assert response.status_code == 200
    spaces = response.json()["payload"]["spaces"]
    assert any(s["_id"] == space_id for s in spaces), f"Space {space_id} not found in list"


# Тест: редактирование имени существующего space
def test_edit_space_name(owner_client, temp_space):
    client = owner_client
    space_id = temp_space

    new_name = generate_project_name()
    response = client.post(**edit_space_endpoint(name=new_name, space_id=space_id))
    assert response.status_code == 200

    response = client.post(**get_space_endpoint(space_id=space_id))
    assert response.status_code == 200
    updated_name = response.json()["payload"]["space"]["name"]
    assert updated_name == new_name


# Тест: имя space не должно быть пустым
def test_space_name_cannot_be_empty(owner_client):
    client = owner_client
    response = client.post(**create_space_endpoint(name=""))
    assert response.status_code == 400, "Should fail if space name is empty"

# Тест: имя space превышает максимальную длину
def test_space_name_length_limit(owner_client):
    client = owner_client
    name = "a" * (MAX_SPACE_NAME_LENGTH + 1)
    response = client.post(**create_space_endpoint(name=name))
    assert response.status_code == 400, "Should fail if space name is too long"

# Тест: удаление space и проверка успешности (без temp_space, так как проверяет удаление)
def test_remove_space_success(owner_client):
    client = owner_client
    name = generate_space_name()

    # Создание space
    create_response = client.post(**create_space_endpoint(name=name))
    assert create_response.status_code == 200, "CreateSpace failed"
    space_id = create_response.json()["payload"]["space"]["_id"]

    # space_id = temp_space

    # Удаление space
    remove_response = client.post(**remove_space_endpoint(space_id=space_id))
    assert remove_response.status_code == 200, "RemoveSpace failed"
    assert remove_response.json()["payload"]["success"], "Expected success=True in RemoveSpace"

    # Проверка: space больше не в списке
    list_response = client.post(**get_spaces_endpoint())
    assert all(s["_id"] != space_id for s in list_response.json()["payload"]["spaces"]), \
        f"Removed space {space_id} всё ещё найден в GetSpaces"

    # Проверка: GetSpace не возвращает удалённый space
    get_response = client.post(**get_space_endpoint(space_id=space_id))
    assert get_response.status_code != 200, "GetSpace по удалённому space вернул 200"
