import allure
import pytest

from config.generators import generate_board_name
from tests.test_backend.data.endpoints.Board.board_endpoints import (
    create_board_custom_field_endpoint,
    create_board_group_endpoint,
)
from tests.test_backend.data.endpoints.Board.custom_field_types import CustomFieldType

from tests.test_backend.data.endpoints.Board.board_endpoints import create_board_endpoint
from tests.test_backend.data.endpoints.Board.constants import (
    MAX_BOARD_NAME_LENGTH,
    BOARD_CUSTOM_FIELD_MAX_DESCRIPTION_LENGTH,
    BOARD_CUSTOM_FIELD_MAX_TITLE_LENGTH,
    BOARD_GROUP_LIMIT_MAX_VALUE,
    BOARD_GROUP_MAX_DESCRIPTION_LENGTH,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'name, expected_status',
    [
        ('', 400),
        (None, 400),
        ('A' * (MAX_BOARD_NAME_LENGTH + 1), 400),
        ('Валидное имя', 200),
        (123, 400),
        ('A' * MAX_BOARD_NAME_LENGTH, 200),
    ],
    ids=['empty string', 'none', 'length > 50', 'valid name', 'number instead of string', 'exactly 50 chars'],
)
def test_board_name_validation(owner_client, temp_project, temp_space, name, expected_status, request):
    allure.dynamic.title(f'Валидация имени борды: {request.node.callspec.id} → ожидали {expected_status}')
    response = owner_client.post(
        **create_board_endpoint(
            name=name, temp_project=temp_project, space_id=temp_space, groups=[], typesList=[], customFields=[]
        )
    )

    with allure.step(f'Проверка, что API вернул статус {expected_status} при {request.node.callspec.id}'):
        assert response.status_code == expected_status


@allure.title('Создание борды с описанием максимальной длины(Поле отсутствует на фронте)')
def test_board_with_max_description(owner_client, temp_project, temp_space):
    name = generate_board_name()
    description = 'D' * BOARD_CUSTOM_FIELD_MAX_DESCRIPTION_LENGTH

    with allure.step(
        f'Отправка запроса на создание борды с описанием длиной {BOARD_CUSTOM_FIELD_MAX_DESCRIPTION_LENGTH} символов'
    ):
        response = owner_client.post(
            **create_board_endpoint(
                name=name,
                temp_project=temp_project,
                space_id=temp_space,
                groups=[],
                typesList=[],
                customFields=[],
                description=description,
            )
        )

    with allure.step('Проверка, что API вернул 200 и описание корректно сохранено'):
        assert response.status_code == 200


@pytest.mark.parametrize(
    'name, expected_status',
    [('', 400), (None, 400), ('A' * 51, 400), ('A' * 50, 200)],
    ids=['empty string', 'None value', 'too long (51 chars)', 'valid name'],
)
def test_board_group_name_validation(owner_client, temp_board, temp_space, name, expected_status, request):
    allure.dynamic.title(f'Валидация поля group name: {request.node.callspec.id} → ожидали {expected_status}')
    response = owner_client.post(
        **create_board_group_endpoint(
            board_id=temp_board, space_id=temp_space, name=name, description='Описание группы'
        )
    )
    with allure.step(f'Проверка, что API вернул {expected_status} при {request.node.callspec.id}'):
        assert response.status_code == expected_status


@pytest.mark.parametrize(
    'description, expected_status',
    [('D' * 1025, 400), ('D' * BOARD_GROUP_MAX_DESCRIPTION_LENGTH, 200), ('Обычное описание', 200), (None, 200)],
    ids=['too long (1025 chars)', 'max valid (1024 chars)', 'regular description', 'None (optional)'],
)
def test_board_group_description_validation(owner_client,temp_board,temp_space,description,expected_status,request):
    allure.dynamic.title(f'Валидация поля group description: {request.node.callspec.id} → ожидали {expected_status}')
    response = owner_client.post(
        **create_board_group_endpoint(
            board_id=temp_board, space_id=temp_space, name='Группа с описанием', description=description
        )
    )
    with allure.step(f'Проверка, что API вернул {expected_status} при {request.node.callspec.id}'):
        assert response.status_code == expected_status


@pytest.mark.parametrize(
    'limit, expected_status',
    [
        pytest.param(-1, 200, marks=pytest.mark.xfail(reason='Бэк принимает отрицательное значение')),
        pytest.param(0, 200, marks=pytest.mark.xfail(reason='Пограничное значение 0 требует уточнения требований')),
        (BOARD_GROUP_LIMIT_MAX_VALUE, 200),
        pytest.param(
            BOARD_GROUP_LIMIT_MAX_VALUE + 1, 200, marks=pytest.mark.xfail(reason='Нет валидации на превышение лимита')
        ),
        (None, 200),
        pytest.param('123', 200, marks=pytest.mark.xfail(reason='Бэк не валидирует тип limit — строка вместо числа')),
    ],
    ids=[
        'limit = -1 (xfail)',
        'limit = 0 (xfail)',
        'limit = 999 (valid)',
        'limit = 1000 (xfail - too much)',
        'limit = None (optional)',
        "limit = '123' (xfail - wrong type)",
    ],
)
@allure.title('Валидация поля limit для board group: {limit}')
def test_board_group_limit_validation(owner_client, temp_board, temp_space, limit, expected_status):
    response = owner_client.post(
        **create_board_group_endpoint(
            board_id=temp_board, space_id=temp_space, name='Группа с лимитом', description='Описание', limit=limit
        )
    )
    with allure.step(f'Проверка, что API вернул {expected_status} при limit = {repr(limit)}'):
        assert response.status_code == expected_status


@pytest.mark.xfail(reason='Известный баг: длинный заголовок custom field без пробелов не влезает в тултип (APP-2763)')
@allure.label('bug', 'APP-2763')
@pytest.mark.parametrize('field_type', CustomFieldType.list())
def test_board_with_long_custom_field_title(owner_client, temp_board, field_type, temp_project, temp_space):
    custom_field = 'T' * (BOARD_CUSTOM_FIELD_MAX_TITLE_LENGTH + 1)

    # Явно указываем тип поля в заголовке
    allure.dynamic.title(f'APP-2763: Ошибка при создании борды с длинным заголовком custom field: {field_type}')

    with allure.step(f'Отправка запроса с custom field title длиннее {BOARD_CUSTOM_FIELD_MAX_TITLE_LENGTH} символов'):
        response = owner_client.post(
            **create_board_custom_field_endpoint(
                board_id=temp_board, name=custom_field, type=field_type, space_id=temp_space
            )
        )

    with allure.step('Проверка, что API вернул 400 – ошибка валидации длины заголовка'):
        assert response.status_code == 400
