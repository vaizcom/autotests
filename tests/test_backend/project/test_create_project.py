import allure
import pytest

from config.generators import generate_project_name, generate_slug
from test_backend.data.endpoints.Project.assert_project_output_payload import assert_project_payload
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    create_project_endpoint
)

pytestmark = [pytest.mark.backend]


@allure.title('Тест: Создание проекта, проверка что payload ответа соответствует ожидаемой структуре')
def test_create_project_output_payload(owner_client, temp_space):
    name = generate_project_name()
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'temporary project', 'space_id': temp_space}
    response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))

    with allure.step("Проверка статуса ответа"):
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"

    with allure.step("Парсинг ответа и проверка полезной нагрузки проекта"):
        payload = response.json()['payload']

        assert_project_payload(payload) # Проверка общей структуры полезной нагрузки

        assert payload['project']['name'] == name, f"Имя проекта в ответе '{payload['project']['name']}' не соответствует ожидаемому '{name}'"
        assert payload['project']['slug'] == slug.upper(), f"slug пространства в ответе '{payload['slug']}' не соответствует ожидаемому '{temp_space}'"