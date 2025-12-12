import allure
import pytest

from config.generators import generate_project_name, generate_slug
from test_backend.data.endpoints.Project.constants import MAX_PROJECT_DESCRIPTION_LENGTH
from test_backend.data.endpoints.Project.project_endpoints import create_project_endpoint

pytestmark = [pytest.mark.backend]

@allure.title('Тест: Проверка предельной длины описания проекта')
def test_project_description_too_long(owner_client, temp_space):
    description = 'D' * (MAX_PROJECT_DESCRIPTION_LENGTH + 1)
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'space_id': temp_space}
    response = owner_client.post(
        **create_project_endpoint(name=name, slug=slug, description=description, **common_kwargs)
    )
    assert response.status_code == 400


@allure.title('Создание проекта с пустым описанием')
def test_project_description_empty(owner_client, temp_space):
    description = ''
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'space_id': temp_space}
    with allure.step('Отправка запроса с пустым описанием проекта'):
        response = owner_client.post(
            **create_project_endpoint(name=name, slug=slug, description=description, **common_kwargs)
        )
    with allure.step('Проверка, что API вернул 200 – описание не является обязательным к заполнению'):
        assert response.status_code == 200

