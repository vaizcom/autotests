import allure
import pytest

from test_backend.project import MAX_PROJECT_SLUG_LENGTH
from tests.config.generators import generate_slug, generate_project_name
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    create_project_endpoint,
    is_project_slug_unique_endpoint
)

pytestmark = [pytest.mark.backend]


@allure.title('Тест: Проверка slug: уникальность до создания, неуникальность после создания, и ошибка при дубликате')
def test_project_slug_unique(owner_client, temp_space):
    client = owner_client
    slug = generate_slug()
    name = generate_project_name()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'test slug validation', 'space_id': temp_space}
    with allure.step('Убедиться, что slug уникален'):
        check_response_1 = client.post(**is_project_slug_unique_endpoint(slug=slug, space_id=temp_space))
    assert check_response_1.status_code == 200
    assert check_response_1.json()['payload']['isUnique'] == True
    with allure.step('Создать проект с этим slug'):
        response_1 = client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response_1.status_code == 200
    with allure.step('Проверить, что slug стал неуникальным'):
        check_response_2 = client.post(**is_project_slug_unique_endpoint(slug=slug, space_id=temp_space))
    assert check_response_2.status_code == 200
    assert check_response_2.json()['payload']['isUnique'] == False
    with allure.step('Попытка создать второй проект с тем же slug'):
        response_2 = client.post(**create_project_endpoint(name=name + '_copy', slug=slug, **common_kwargs))
    assert response_2.status_code == 400
    r = response_2.json()
    assert response_2.json()['error']['code'] == 'InvalidForm'


@allure.title('Тест: Проверка предельной длины slug')
def test_project_slug_too_long(owner_client, temp_space):
    slug = generate_slug(MAX_PROJECT_SLUG_LENGTH + 1, MAX_PROJECT_SLUG_LENGTH + 1)
    name = generate_project_name()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'too long slug', 'space_id': temp_space}
    response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 400


@allure.title('Создание проекта с пустым slug')
def test_project_slug_empty(owner_client, temp_space):
    slug = ''
    name = generate_project_name()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'empty slug', 'space_id': temp_space}
    with allure.step('Отправка запроса с пустым slug проекта'):
        response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    with allure.step('Проверка, что API вернул 404 – ошибка валидации'):
        assert response.status_code == 400


@allure.title('Создание проекта с невалидным slug (не латиница)')
def test_project_slug_only_latin_letter(owner_client, temp_space):
    slug = 'некорректный'
    name = generate_project_name()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'нелатинский slug', 'space_id': temp_space}

    with allure.step('Отправка запроса с кириллическим slug'):
        response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))

    with allure.step('Проверка, что API вернул 400 – slug должен быть на латинице'):
        assert response.status_code == 400