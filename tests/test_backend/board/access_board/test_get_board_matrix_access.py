import pytest
import allure

from tests.test_backend.data.endpoints.Board.board_endpoints import (
    get_board_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 200),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_get_board_access_by_roles(request, client_fixture, expected_status, board_with_tasks, main_space):
    allure.dynamic.title(f'Тест получения доски: клиент={client_fixture}, ожидаемый статус={expected_status}')

    with allure.step(f'Получение клиента: {client_fixture}'):
        client = request.getfixturevalue(client_fixture)

    with allure.step("Отправка запроса на получение борды"):
        payload = get_board_endpoint(
            space_id=main_space,
            board_id=board_with_tasks
        )
        response = client.post(**payload)

    with allure.step(f'Проверка статус-кода: ожидаемый {expected_status}'):
        assert response.status_code == expected_status, response.text


@pytest.mark.parametrize(
    'client_fixture, expected_status, expected_error_code',
    [
        ('foreign_client', 403, 'AccessDenied'),  # Пользователь не имеет доступа к space
        ('client_with_access_only_in_space', 403, 'AccessDenied'),  # Пользователь имеет доступ к space, но не к проекту и борде
        ('client_with_access_only_in_project', 403, 'AccessDenied'),  # Пользователь имеет доступ к space и проекту, но не к борде
    ],
    ids=['foreign_client', 'space_client', 'project_client'],
)
def test_negative_access_to_board(
    request, client_fixture, expected_status, expected_error_code, main_board, main_space
):
    """
    Test to verify negative access scenarios for a board.

    """
    allure.dynamic.title(
        f'Негативный тест на доступ к борде: клиент={client_fixture}, ожидаемый статус={expected_status}'
    )

    with allure.step(f'Получение клиента: {client_fixture}'):
        client = request.getfixturevalue(client_fixture)

    with allure.step(f"Отправка запроса на получение данных борды с ID '{main_board}'"):
        payload = get_board_endpoint(board_id=main_board, space_id=main_space)
        response = client.post(**payload)

    with allure.step(f'Проверка статус-кода: ожидаемый {expected_status}'):
        assert response.status_code == expected_status, response.text

    with allure.step('Проверка структуры ответа'):
        response_json = response.json()
        assert 'payload' in response_json, "Отсутствует ключ 'payload' в ответе"
        assert 'error' in response_json, "Отсутствует ключ 'error' в ответе"
        assert 'type' in response_json, "Отсутствует ключ 'type' в ответе"

    with allure.step("Проверка значения 'payload' (должно быть null)"):
        assert response_json['payload'] is None, "Ожидался 'null' в поле 'payload'"

    with allure.step("Проверка ошибки в поле 'error'"):
        error = response_json['error']
        assert 'code' in error, "Отсутствует ключ 'code' в 'error'"
        assert 'originalType' in error, "Отсутствует ключ 'originalType' в 'error'"
        assert (
            error['code'] == expected_error_code
        ), f"Ожидался код ошибки '{expected_error_code}', но получен '{error['code']}'"
        assert (
            error['originalType'] == 'GetBoard'
        ), f"Ожидался originalType 'GetBoard', но получен '{error['originalType']}'"

    with allure.step("Проверка значения 'type'"):
        assert response_json['type'] == 'GetBoard', f"Ожидался 'type'='GetBoard', но получен '{response_json['type']}'"
