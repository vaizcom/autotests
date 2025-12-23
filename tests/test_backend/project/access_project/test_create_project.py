import pytest
import allure

from config.generators import generate_project_name, generate_slug
from test_backend.data.endpoints.Project.project_endpoints import create_project_endpoint, archive_project_endpoint

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Project Service")
@allure.suite("Access project")
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
def test_create_project_access_by_roles(request, client_fixture, expected_status, main_space):
    allure.dynamic.title(f'Create project: клиент={client_fixture}, ожидаемый статус={expected_status}')
    prj_id = None
    try:
        client = request.getfixturevalue(client_fixture)
        name = generate_project_name()
        slug = generate_slug()
        common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'temporary project'}
        with allure.step("Отправка запроса на создание project"):
            response = client.post(**create_project_endpoint(name=name, slug=slug, space_id=main_space, **common_kwargs))
        with allure.step(f'Проверка статус-кода: ожидаемый {expected_status}'):
            assert response.status_code == expected_status, response.text
        if expected_status == 200:
            prj_id = response.json()['payload']['project']['_id']
            with allure.step('Проверка, что проект был создан'):
                assert response.json()['payload']['project']['name'] == name
                assert response.json()['payload']['project']['slug'] == slug.upper()
    finally:
        if prj_id:  # Если проект был создан, архивируем его (в созданном проекте пользователь становится в роли оунера)
            with allure.step('Архивирование проекта'):
                client.post(**archive_project_endpoint(project_id=prj_id, space_id=main_space))