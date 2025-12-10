import pytest
import allure

from test_backend.data.endpoints.Project.project_endpoints import get_project_endpoint

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
def test_get_project_access_by_roles(request, client_fixture, expected_status, main_project, main_space):
    allure.dynamic.title(f'Тест получения project: клиент={client_fixture}, ожидаемый статус={expected_status}')

    with allure.step(f'Получение клиента: {client_fixture}'):
        client = request.getfixturevalue(client_fixture)

    with allure.step(f"Отправка запроса на получение project"):
        payload = get_project_endpoint(
            project_id=main_project,
            space_id=main_space
        )
        response = client.post(**payload)

    with allure.step(f'Проверка статус-кода: ожидаемый {expected_status}'):
        assert response.status_code == expected_status, response.text


@pytest.mark.parametrize(
    'client_fixture, expected_status, expected_error_code',
    [
        ('foreign_client', 403, 'AccessDenied'),  # Пользователь не имеет доступа к space
        ('client_with_access_only_in_space', 403, 'AccessDenied'),  # Пользователь имеет доступ к space, но не к проекту
    ],
    ids=['foreign_client', 'space_client'],
)
def test_negative_access_to_project(
    request, client_fixture, expected_status, expected_error_code, main_project, main_space
):
    """
    Test to verify negative access scenarios for Project

    """
    allure.dynamic.title(
        f'Негативный тест на доступ к борде: клиент={client_fixture}, ожидаемый статус={expected_status}'
    )

    with allure.step(f'Получение клиента: {client_fixture}'):
        client = request.getfixturevalue(client_fixture)

    with allure.step(f"Отправка запроса на получение данных projectID"):
        payload = get_project_endpoint(
            project_id=main_project,
            space_id=main_space
        )
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
            error['originalType'] == 'GetProject'
        ), f"Ожидался originalType 'GetProject', но получен '{error['originalType']}'"

    with allure.step("Проверка значения 'type'"):
        assert response_json['type'] == 'GetProject', f"Ожидался 'type'='GetProject', но получен '{response_json['type']}'"
