from backend_tests.core.client import APIClient
from backend_tests.core.auth import get_token
from backend_tests.config.settings import API_URL
from backend_tests.utils.generators import generate_space_name
import pytest
from backend_tests.data.endpoints.Space.space_endpoints import (
    create_space_endpoint,
    remove_space_endpoint
)


@pytest.fixture
def guest_client():
    return APIClient(base_url=API_URL, token=get_token("guest"))

@pytest.fixture
def member_client():
    return APIClient(base_url=API_URL, token=get_token("member"))

@pytest.fixture
def manager_client():
    return APIClient(base_url=API_URL, token=get_token("manager"))


# Фикстура: возвращает авторизованного API клиента с токеном владельца
@pytest.fixture(scope="module")
def owner_client():
    token = get_token("owner")
    return APIClient(base_url=API_URL, token=token)

# Фикстура: создает временный спейс и после прохождения тестов удаляет этот временный спейс
@pytest.fixture(scope="module")
def temp_space(owner_client):
    client = owner_client
    name = generate_space_name()
    response = client.post(**create_space_endpoint(name=name))
    assert response.status_code == 200
    space_id = response.json()["payload"]["space"]["_id"]

    yield space_id

    client.post(**remove_space_endpoint(space_id=space_id))

# # Фикстура: Возвращает заранее известный ID space
# @pytest.fixture(scope="module")
# def temp_space1():
#     """
#     Возвращает заранее известный ID space, например для интеграционных тестов.
#     """
#     return "681b18bd0305fa9c5f83fd85"

