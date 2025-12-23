import allure
import pytest

from config.generators import generate_slug
from test_backend.data.endpoints.Project.project_endpoints import create_project_endpoint
from test_backend.project import MAX_PROJECT_NAME_LENGTH

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Project Service")
@allure.suite("Validation project")
@allure.title('Validation project name: Проверка предельной длины имени проекта')
def test_project_name_too_long(owner_client, temp_space):
    name = 'P' * (MAX_PROJECT_NAME_LENGTH + 1)
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'too long name', 'space_id': temp_space}
    response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 400


@allure.parent_suite("Project Service")
@allure.suite("Validation project")
@allure.title('Validation project empty name: Создание проекта с пустым названием')
def test_project_name_empty(owner_client, temp_space):
    name = ''
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'too long name', 'space_id': temp_space}
    with allure.step('Отправка запроса с пустым названием проекта'):
        response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    with allure.step('Проверка, что API вернул 404 – ошибка валидации'):
        assert response.status_code == 400