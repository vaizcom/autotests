import allure
import pytest
from tests.config.generators import generate_board_name, generate_custom_field_title, generate_object_id
from tests.test_backend.data.endpoints.Board.board_endpoints import (
    create_board_endpoint,
    create_board_custom_field_endpoint,
    edit_board_custom_field_endpoint,
    get_board_endpoint,
    edit_board_endpoint,
    create_board_group_endpoint,
    edit_board_group_endpoint,
)
from tests.test_backend.data.endpoints.Board.custom_field_types import CustomFieldType


pytestmark = [pytest.mark.backend]


@allure.parent_suite("Board Service")
@allure.title('Создание борды в существующем проекте и корректность возвращаемого имени')
def test_create_board(owner_client, temp_project, temp_space):
    # Генерация имени борды
    name = generate_board_name()
    # Отправка запроса и проверка результата
    with allure.step('Отправка запроса на создание борды с валидными данными'):
        response = owner_client.post(**create_board_endpoint(name, temp_project, temp_space, [], [], []))

    # Проверяем статус и возвращаемое имя борды
    with allure.step('Проверка успешного ответа от API'):
        assert response.status_code == 200, f'Ошибка: {response.text}'

    with allure.step('Проверка корректности имени созданной борды'):
        response_data = response.json()
        assert 'payload' in response_data, "Ошибка: В ответе отсутствует поле 'payload'"
        assert 'board' in response_data['payload'], "Ошибка: В 'payload' отсутствует объект 'board'"
        assert (
            response_data['payload']['board']['name'] == name
        ), f"Ожидалось имя борды '{name}', а получено '{response_data['payload']['board']['name']}'"


@allure.parent_suite("Board Service")
@allure.title('Создание нескольких борд с одинаковым именем в одном проекте')
def test_create_board_with_duplicate_name_allowed(owner_client, temp_project, temp_space):
    name = generate_board_name()

    with allure.step('Создание первой борды с именем'):
        response1 = owner_client.post(**create_board_endpoint(name, temp_project, temp_space, [], [], []))
        assert response1.status_code == 200

    with allure.step('Повторная попытка создать борду с тем же именем'):
        response2 = owner_client.post(**create_board_endpoint(name, temp_project, temp_space, [], [], []))

    with allure.step('Проверка, что API вернул 200'):
        assert response2.status_code == 200


@allure.parent_suite("Board Service")
@allure.title('Ошибка при создании борды с None вместо списков в полях groups/typesList/customFields')
def test_create_board_with_none_fields(owner_client, temp_project, temp_space):
    name = generate_board_name()

    with allure.step('Отправка запроса, где списочные поля переданы как None'):
        response = owner_client.post(**create_board_endpoint(name, temp_project, temp_space, None, None, None))

    with allure.step('Проверка, что API вернул 400 – ошибка валидации типов'):
        assert response.status_code == 400


@allure.parent_suite("Board Service")
@allure.title('Редактирование борды: изменение имени через /EditBoard')
def test_edit_board_name(owner_client, temp_board, temp_space):
    new_name = generate_board_name()

    with allure.step('Редактирование борды с новым именем'):
        response = owner_client.post(**edit_board_endpoint(board_id=temp_board, name=new_name, space_id=temp_space))
        assert response.status_code == 200

    with allure.step('Получение борды по ID и проверка обновлённого имени'):
        get_response = owner_client.post(**get_board_endpoint(board_id=temp_board, space_id=temp_space))
        assert get_response.status_code == 200
        board = get_response.json()['payload']['board']
        assert board['name'] == new_name, f"Ожидалось имя '{new_name}', получено '{board['name']}'"


@allure.parent_suite("Board Service")
@allure.title(
    'Добавление новой группы в борду через /CreateBoardGroup: проверка имени, описания и изменения количества групп'
)
def test_create_board_group(owner_client, temp_board, temp_space):
    new_group_name = 'Созданная группа'
    new_group_description = 'Описание новой группы'

    with allure.step('Шаг 1: Получаем список групп до создания новой'):
        get_before = owner_client.post(**get_board_endpoint(temp_board, temp_space))
        assert get_before.status_code == 200
        board_before = get_before.json()['payload']['board']
        groups_before = board_before.get('groups', [])
        count_before = len(groups_before)

    with allure.step('Шаг 2: Отправляем запрос на создание новой группы'):
        create_response = owner_client.post(
            **create_board_group_endpoint(
                board_id=temp_board, space_id=temp_space, name=new_group_name, description=new_group_description
            )
        )
        assert create_response.status_code == 200

    with allure.step('Шаг 3: Получаем список групп после создания'):
        get_after = owner_client.post(**get_board_endpoint(temp_board, temp_space))
        assert get_after.status_code == 200
        board_after = get_after.json()['payload']['board']
        groups_after = board_after.get('groups', [])
        count_after = len(groups_after)

    with allure.step('Шаг 4: Проверяем, что количество групп увеличилось на 1'):
        assert count_after == count_before + 1, f'Ожидалось {count_before + 1} групп, но получено {count_after}'

    with allure.step('Шаг 5: Проверяем, что новая группа (new_group_name) действительно добавлена'):
        names_after = [group['name'] for group in groups_after]
        assert new_group_name in names_after, f"Группа '{new_group_name}' не найдена среди {names_after}"

    with allure.step('Шаг 6: Проверяем описание (new_group_description) новой группы'):
        created_group = None
        for group in groups_after:
            if group['name'] == new_group_name:
                created_group = group
                break
        assert created_group is not None, f"Группа '{new_group_name}' не найдена после создания"
        assert created_group.get('description') == new_group_description, (
            f"Описание не совпадает: ожидалось '{new_group_description}', "
            f"получено '{created_group.get('description')}'"
        )


@allure.parent_suite("Board Service")
@allure.title('Редактирование группы через /EditBoardGroup: проверка обновления имени, описания, лимита и скрытия')
def test_edit_board_group_updates_fields(owner_client, temp_board, temp_space):
    original_name = 'Группа для редактирования'
    original_description = 'Исходное описание'

    with allure.step('Шаг 1: Создание новой группы, которую затем будем редактировать'):
        create_response = owner_client.post(
            **create_board_group_endpoint(
                board_id=temp_board, space_id=temp_space, name=original_name, description=original_description
            )
        )
        assert create_response.status_code == 200, 'Ошибка при создании группы'

        groups = create_response.json()['payload']['boardGroups']
        group_to_edit = None
        for group in groups:
            if group['name'] == original_name:
                group_to_edit = group
                break

        assert group_to_edit is not None, f"Группа '{original_name}' не найдена после создания"
        group_id = group_to_edit['_id']

    updated_name = 'Новое имя'
    updated_description = 'Новое описание'
    updated_limit = 5
    updated_hidden = True

    with allure.step('Шаг 2: Редактирование группы через /EditBoardGroup'):
        edit_response = owner_client.post(
            **edit_board_group_endpoint(
                board_id=temp_board,
                board_group_id=group_id,
                space_id=temp_space,
                name=updated_name,
                description=updated_description,
                limit=updated_limit,
                hidden=updated_hidden,
            )
        )
        assert edit_response.status_code == 200, 'Редактирование завершилось с ошибкой'

    with allure.step('Шаг 3: Получение борды и проверка обновлённых данных группы'):
        get_response = owner_client.post(**get_board_endpoint(temp_board, temp_space))
        assert get_response.status_code == 200, 'Ошибка при получении борды'

        updated_groups = get_response.json()['payload']['board']['groups']
        updated_group = None
        for group in updated_groups:
            if group['_id'] == group_id:
                updated_group = group
                break

        assert updated_group is not None, 'Обновлённая группа не найдена'

        assert (
            updated_group['name'] == updated_name
        ), f"Имя не обновлено: ожидалось '{updated_name}', получено '{updated_group['name']}'"
        assert updated_group.get('description') == updated_description, 'Описание не совпадает'
        assert updated_group.get('limit') == updated_limit, 'Лимит не обновлён'
        assert updated_group.get('hidden') is True, "Поле 'hidden' не обновлено на True"



@allure.parent_suite("Board Service")
@pytest.mark.parametrize('field_type', CustomFieldType.list())
@allure.title('Создание кастомного поля типа: {field_type}')
def test_create_custom_field_of_each_type(owner_client, temp_board, field_type, temp_space):
    title = generate_custom_field_title()

    with allure.step(f"Создание поля типа '{field_type}' с валидным заголовком"):
        response = owner_client.post(
            **create_board_custom_field_endpoint(board_id=temp_board, name=title, type=field_type, space_id=temp_space)
        )

    with allure.step('Проверка, что API вернул 200'):
        assert response.status_code == 200
        assert response.json()['payload']['customField']['name'] == title
        assert response.json()['payload']['customField']['type'] == field_type


@allure.parent_suite("Board Service")
@pytest.mark.parametrize('field_type', [t.value for t in CustomFieldType if t.value != 'Select'])
@allure.title('Редактирование кастомного поля типа: {field_type}')
def test_edit_custom_field_common_fields(owner_client, temp_board, temp_space, field_type):
    original_title = generate_custom_field_title()

    with allure.step(f"Создание поля типа '{field_type}'"):
        create_response = owner_client.post(
            **create_board_custom_field_endpoint(
                board_id=temp_board, name=original_title, type=field_type, space_id=temp_space
            )
        )
        assert create_response.status_code == 200
        field_id = create_response.json()['payload']['customField']['_id']

    new_name = 'Обновлённое имя'
    new_description = 'Обновлённое описание'
    hidden = True

    with allure.step('Редактирование поля: обновление name, description и hidden'):
        edit_response = owner_client.post(
            **edit_board_custom_field_endpoint(
                board_id=temp_board,
                field_id=field_id,
                name=new_name,
                description=new_description,
                hidden=hidden,
                space_id=temp_space,
            )
        )

    with allure.step('Проверка успешного редактирования'):
        assert edit_response.status_code == 200
        updated_field = edit_response.json()['payload']['customField']
        assert updated_field['name'] == new_name
        assert updated_field['description'] == new_description
        assert updated_field['hidden'] is True


@allure.parent_suite("Board Service")
@allure.title('Редактирование поля Select: добавление новых опций с валидным _id')
def test_edit_select_custom_field(owner_client, temp_board, temp_space):
    title = generate_custom_field_title()

    with allure.step("Создание поля типа 'Select' без опций"):
        create_response = owner_client.post(
            **create_board_custom_field_endpoint(
                board_id=temp_board, space_id=temp_space, name=title, type=CustomFieldType.SELECT.value
            )
        )
        assert create_response.status_code == 200, f'Create failed: {create_response.json()}'
        field_id = create_response.json()['payload']['customField']['_id']

    new_title = 'Обновлённое имя'
    new_options = [
        {'_id': generate_object_id(), 'title': 'Опция 1', 'color': 'red', 'icon': 'Thumb'},
        {'_id': generate_object_id(), 'title': 'Опция 2', 'color': 'Cursor'},
    ]

    with allure.step('Редактирование поля: добавление опций'):
        edit_response = owner_client.post(
            **edit_board_custom_field_endpoint(
                board_id=temp_board,
                space_id=temp_space,
                field_id=field_id,
                name=new_title,
                hidden=True,
                options=new_options,
            )
        )
        assert edit_response.status_code == 200, f'Edit failed: {edit_response.json()}'

        data = edit_response.json()['payload']['customField']
        assert data['name'] == new_title
        assert len(data['options']) == 2
        assert data['options'][0]['title'] == 'Опция 1'