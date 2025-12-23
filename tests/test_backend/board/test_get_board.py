import allure
import pytest
from tests.config.generators import generate_board_name
from tests.test_backend.data.endpoints.Board.board_endpoints import (
    create_board_endpoint,
    get_board_endpoint,
)

pytestmark = [pytest.mark.backend]

@allure.parent_suite("Board Service")
@allure.title('Получение борды по boardId через /GetBoard')
def test_get_board_by_id(owner_client, temp_project, temp_space):
    name = generate_board_name()

    with allure.step('Создание борды'):
        create_response = owner_client.post(**create_board_endpoint(name, temp_project, temp_space, [], [], []))
        assert create_response.status_code == 200
        board_id = create_response.json()['payload']['board']['_id']

    with allure.step('Получение борды по boardId через /GetBoard'):
        get_response = owner_client.post(**get_board_endpoint(board_id, temp_space))
        assert get_response.status_code == 200

        board = get_response.json()['payload']['board']
        assert board['name'] == name
        assert board['_id'] == board_id
        assert board['project'] == temp_project

@allure.parent_suite("Board Service")
@allure.title('Ошибка при попытке получить борду по несуществующему boardId')
def test_get_board_with_invalid_id(owner_client, temp_space):
    fake_board_id = 'non_existing_board_id_12345'

    with allure.step('Попытка получить борду по несуществующему boardId'):
        response = owner_client.post(**get_board_endpoint(board_id=fake_board_id, space_id=temp_space))

    with allure.step('Проверка, что API вернул ошибку 400 или 404'):
        assert (
            response.status_code == 400
        ), f'Ожидался статус 400, но получен {response.status_code} с ответом: {response.text}'
