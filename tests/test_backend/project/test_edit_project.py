import allure
import pytest

from tests.config.generators import generate_project_name
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    edit_project_endpoint,
)

pytestmark = [pytest.mark.backend]


@allure.title('Тест: Проверка редактирования имени проекта')
def test_edit_project_name(owner_client, temp_project, temp_space):
    client = owner_client
    new_name = generate_project_name()
    edit_response = client.post(**edit_project_endpoint(project_id=temp_project, name=new_name, space_id=temp_space))
    assert edit_response.status_code == 200
    assert edit_response.json()['payload']['project']['name'] == new_name