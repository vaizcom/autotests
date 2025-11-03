import allure
import pytest
from config.generators import generate_board_name
from tests.test_backend.data.endpoints.Board.board_endpoints import (
    create_board_endpoint,
    get_boards_endpoint,
)

pytestmark = [pytest.mark.backend]


@allure.title('Получение списка борд: проверка, что все созданные борды присутствуют в ответе(board_names)')
def test_get_boards_returns_multiple_created_boards(owner_client, temp_project, temp_space):
    board_names = [generate_board_name() for _ in range(3)]

    with allure.step('Создание трёх борд'):
        for name in board_names:
            response = owner_client.post(**create_board_endpoint(name, temp_project, temp_space, [], [], []))
            assert response.status_code == 200, f"Не удалось создать борду '{name}'"

    with allure.step('Запрос всех борд в текущем спейсе'):
        get_response = owner_client.post(**get_boards_endpoint(temp_space))
        assert get_response.status_code == 200

    boards = get_response.json()['payload']['boards']
    board_names_in_response = [b['name'] for b in boards]

    with allure.step('Проверка, что все созданные борды присутствуют в ответе(board_names)'):
        for name in board_names:
            assert name in board_names_in_response, f"Борда '{name}' не найдена в списке"


@allure.title('Получение списка борд: проверка созданных борд и их обязательных полей(name, projectId, createdAt)')
def test_get_boards_required_fields(owner_client, temp_project, temp_space):
    board_names = [generate_board_name() for _ in range(3)]

    with allure.step('Создание трёх борд'):
        for name in board_names:
            response = owner_client.post(**create_board_endpoint(name, temp_project, temp_space, [], [], []))
            assert response.status_code == 200, f"Не удалось создать борду '{name}'"

    with allure.step('Запрос всех борд в текущем спейсе'):
        get_response = owner_client.post(**get_boards_endpoint(temp_space))
        assert get_response.status_code == 200

    boards = get_response.json()['payload']['boards']
    board_map = {b['name']: b for b in boards if b['name'] in board_names}

    with allure.step('Проверка, что все созданные борды присутствуют в ответе и содержат нужные поля'):
        for name in board_names:
            assert name in board_map, f"Борда '{name}' не найдена в списке"
            board = board_map[name]
            assert board.get('project') == temp_project, f"projectId борды '{name}' не совпадает"
            assert 'createdAt' in board, f"У борды '{name}' отсутствует поле createdAt"
            assert isinstance(board['createdAt'], str), 'Поле createdAt должно быть строкой (ISO формат)'
