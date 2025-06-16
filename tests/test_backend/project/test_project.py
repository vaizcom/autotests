import allure

from config.generators import generate_slug, generate_project_name
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    create_project_endpoint,
    edit_project_endpoint,
    get_project_endpoint,
    get_projects_endpoint,
    archive_project_endpoint,
    unarchive_project_endpoint,
    is_project_slug_unique_endpoint,
    MAX_PROJECT_NAME_LENGTH,
    MAX_PROJECT_DESCRIPTION_LENGTH,
    MAX_PROJECT_SLUG_LENGTH,
)
import pytest

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
    assert check_response_1.json()['payload']['isUnique']
    with allure.step('Создать проект с этим slug'):
        response_1 = client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response_1.status_code == 200
    with allure.step('Проверить, что slug стал неуникальным'):
        check_response_2 = client.post(**is_project_slug_unique_endpoint(slug=slug, space_id=temp_space))
    assert check_response_2.status_code == 200
    assert not check_response_2.json()['payload']['isUnique']
    with allure.step('Попытка создать второй проект с тем же slug'):
        response_2 = client.post(**create_project_endpoint(name=name + '_copy', slug=slug, **common_kwargs))
    assert response_2.status_code == 400


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


@allure.title('Тест: Проверка предельной длины имени проекта')
def test_project_name_too_long(owner_client, temp_space):
    name = 'P' * (MAX_PROJECT_NAME_LENGTH + 1)
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'too long name', 'space_id': temp_space}
    response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    assert response.status_code == 400


@allure.title('Создание проекта с пустым названием')
def test_project_name_empty(owner_client, temp_space):
    name = ''
    slug = generate_slug()
    common_kwargs = {'color': 'blue', 'icon': 'Dot', 'description': 'too long name', 'space_id': temp_space}
    with allure.step('Отправка запроса с пустым названием проекта'):
        response = owner_client.post(**create_project_endpoint(name=name, slug=slug, **common_kwargs))
    with allure.step('Проверка, что API вернул 404 – ошибка валидации'):
        assert response.status_code == 400


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


@allure.title('Тест: Проверка получения проекта по ID')
def test_get_project(owner_client, temp_project, temp_space):
    client = owner_client
    response = client.post(**get_project_endpoint(project_id=temp_project, space_id=temp_space))
    assert response.status_code == 200
    payload = response.json()['payload']
    assert 'project' in payload


@allure.title('Тест: Проверка списка проектов')
def test_get_projects(owner_client, temp_project, temp_space):
    client = owner_client
    response = client.post(**get_projects_endpoint(space_id=temp_space))
    assert response.status_code == 200
    projects = response.json()['payload']['projects']
    project_ids = [p['_id'] for p in projects]
    assert temp_project in project_ids


@allure.title('Тест: Проверка редактирования имени проекта')
def test_edit_project_name(owner_client, temp_project, temp_space):
    client = owner_client
    new_name = generate_project_name()
    edit_response = client.post(**edit_project_endpoint(project_id=temp_project, name=new_name, space_id=temp_space))
    assert edit_response.status_code == 200
    assert edit_response.json()['payload']['project']['name'] == new_name


@allure.title('Тест: Проверка архивации проекта')
def test_archive_project(owner_client, temp_project, temp_space):
    client = owner_client
    archive_response = client.post(**archive_project_endpoint(project_id=temp_project, space_id=temp_space))
    assert archive_response.status_code == 200
    assert archive_response.json()['payload']['project'].get('archivedAt')


@allure.title('Тест: Проверка разархивации проекта')
def test_unarchive_project(owner_client, temp_project, temp_space):
    client = owner_client
    client.post(**archive_project_endpoint(project_id=temp_project, space_id=temp_space))
    unarchive_response = client.post(**unarchive_project_endpoint(project_id=temp_project, space_id=temp_space))
    assert unarchive_response.status_code == 200
    assert unarchive_response.json()['payload'].get('itemId') == temp_project
