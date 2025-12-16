import allure
import pytest

from tests.config.generators import generate_project_name, generate_slug, generate_project_description
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    edit_project_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 403),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_edit_project_name_access_by_roles(request, client_fixture, expected_status, main_project_2, main_space):
    allure.dynamic.title(f'Тест редактирования project: клиент={client_fixture}, ожидаемый статус={expected_status}')
    client = request.getfixturevalue(client_fixture)
    new_name = generate_project_name()+"_new"
    with allure.step(f"Отправка запроса на редактирование project с новым именем: {new_name}"):
        edit_response = client.post(**edit_project_endpoint(project_id=main_project_2, name=new_name, space_id=main_space))
    with allure.step(f'Проверка статус-кода: ожидаемый {expected_status}'):
        assert edit_response.status_code == expected_status, edit_response.text
        r =edit_response.json()['payload']
    if expected_status == 200:
        with allure.step('Проверка, что имя проекта было обновлено'):
            assert edit_response.json()['payload']['project']['name'] == new_name


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 403),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_edit_project_slug_access_by_roles(request, client_fixture, expected_status, main_project_2, main_space):
    allure.dynamic.title(f'Тест редактирования project: клиент={client_fixture}, ожидаемый статус={expected_status}')
    client = request.getfixturevalue(client_fixture)
    new_slug = generate_slug()
    with allure.step(f"Отправка запроса на редактирование project с новым именем: {new_slug}"):
        edit_response = client.post(**edit_project_endpoint(project_id=main_project_2, slug=new_slug, space_id=main_space))
    with allure.step(f'Проверка статус-кода: ожидаемый {expected_status}'):
        assert edit_response.status_code == expected_status, edit_response.text
        r =edit_response.json()['payload']
    if expected_status == 200:
        with allure.step('Проверка, что имя проекта было обновлено'):
            assert edit_response.json()['payload']['project']['slug'] == new_slug.upper()


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 403),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_edit_project_description_access_by_roles(request, client_fixture, expected_status, main_project_2, main_space):
    allure.dynamic.title(f'Тест редактирования project: клиент={client_fixture}, ожидаемый статус={expected_status}')
    client = request.getfixturevalue(client_fixture)
    new_description = generate_project_description()
    with allure.step(f"Отправка запроса на редактирование project с новым именем: {new_description}"):
        edit_response = client.post(**edit_project_endpoint(project_id=main_project_2, description=new_description, space_id=main_space))
    with allure.step(f'Проверка статус-кода: ожидаемый {expected_status}'):
        assert edit_response.status_code == expected_status, edit_response.text
        r =edit_response.json()['payload']
    if expected_status == 200:
        with allure.step('Проверка, что имя проекта было обновлено'):
            assert edit_response.json()['payload']['project']['description'] == new_description