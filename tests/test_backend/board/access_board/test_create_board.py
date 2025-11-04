import pytest
import uuid
import allure

from tests.test_backend.data.endpoints.Board.board_endpoints import (
    create_board_endpoint,
    delete_board_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 403),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_create_board_access_by_roles(request, client_fixture, expected_status, main_project, main_space):
    allure.dynamic.title(f'Тест создания доски: клиент={client_fixture}, ожидаемый статус={expected_status}')

    with allure.step(f'Получение клиента: {client_fixture}'):
        client = request.getfixturevalue(client_fixture)

    with allure.step('Генерация уникального имени доски'):
        board_name = f'board_{uuid.uuid4().hex[:8]}'
        allure.attach(board_name, name='Сгенерированное имя доски', attachment_type=allure.attachment_type.TEXT)

    with allure.step(f"Отправка запроса на создание доски с именем '{board_name}'"):
        payload = create_board_endpoint(
            name=board_name,
            project=main_project,
            space_id=main_space,
            groups=[],
            typesList=[],
            customFields=[],
        )
        response = client.post(**payload)

    with allure.step(f'Проверка статус-кода: ожидаемый {expected_status}'):
        assert response.status_code == expected_status, response.text
    if response.status_code == 200:
        with allure.step('Обработка созданной доски'):
            board_id = response.json()['payload']['board']['_id']
            board_name = response.json()['payload']['board']['name']

            with allure.step(f"Удаление доски '{board_name}' (ID: {board_id})"):
                delete_payload = delete_board_endpoint(board_id=board_id, board_name=board_name, space_id=main_space)
                delete_response = client.post(**delete_payload)
                assert delete_response.status_code == 200, 'Ошибка при удалении доски'
