import allure
import pytest

from conftest import main_project_2
from tests.test_backend.data.endpoints.Project.project_endpoints import (
    get_project_endpoint,
    archive_project_endpoint,
    unarchive_project_endpoint
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
@allure.title('Тест: Проверка архивации и разархивации проекта по ролям')
def test_archive_unarchive_project(request, client_fixture, expected_status, owner_client, main_space, main_project_2):
    allure.dynamic.title(f'Тест архивации и разархивации project: клиент={client_fixture}, ожидаемый статус={expected_status}')
    client = request.getfixturevalue(client_fixture)

    with allure.step(f'Шаг 1. Подготовка к тесту: Проверка и сброс состояния проекта (если архивирован) для {client_fixture}'):
        # Получаем текущее состояние проекта
        current_get_response = owner_client.post(**get_project_endpoint(project_id=main_project_2, space_id=main_space))

        project_needs_unarchive = False
        if current_get_response.status_code == 400:
            error_code = current_get_response.json().get('error', {}).get('code')
            assert error_code == 'ItemInArchive', f"Неожиданная ошибка при получении проекта"
            project_needs_unarchive = True
        elif current_get_response.status_code == 200:
            current_project_data = current_get_response.json()['payload']['project']
            if current_project_data.get('archivedAt') is not None:
                print("Проект архивирован (archivedAt не None), необходимо разархивировать.")
                project_needs_unarchive = True
        else:
            pytest.fail(f"Неожиданный статус код ({current_get_response.status_code})")

        if project_needs_unarchive:
            unarchive_initially_response = owner_client.post(**unarchive_project_endpoint(project_id=main_project_2, space_id=main_space))
            assert unarchive_initially_response.status_code == 200, f"Не удалось разархивировать проект перед тестом: {unarchive_initially_response.text}"

        # Подтверждаем, что проект разархивирован перед продолжением теста
        final_initial_check_response = owner_client.post(**get_project_endpoint(project_id=main_project_2, space_id=main_space))
        assert final_initial_check_response.status_code == 200, f"Проект недоступен после попытки разархивации: {final_initial_check_response.text}"
        final_initial_project_data = final_initial_check_response.json()['payload']['project']
        assert final_initial_project_data.get('archivedAt') is None, "Проект не был разархивирован перед тестом."

    with allure.step(f'Шаг 2: Попытка архивировать проект с ролью {client_fixture}, ожидаемый статус={expected_status}'):
        archive_response = client.post(**archive_project_endpoint(project_id=main_project_2, space_id=main_space))
        assert archive_response.status_code == expected_status, \
            f"Ожидался статус {expected_status} для архивации, получен {archive_response.status_code} ({archive_response.text})"
        if expected_status != 200:
            assert archive_response.json().get('error', {}).get('code') == 'AccessDenied'

        if expected_status == 200:
            # Если архивация успешна, проверяем, что project.archivedAt не None в ответе на архивацию
            project_data_after_archive = archive_response.json()['payload']['project']
            assert project_data_after_archive.get('archivedAt') is not None, "Поле 'archivedAt' должно быть не None после успешной архивации."

            # Также проверяем, что GET запрос на этот проект вернет 400 с ошибкой ItemInArchive
            get_archived_project_response = client.post(**get_project_endpoint(project_id=main_project_2, space_id=main_space))
            assert get_archived_project_response.status_code == 400, f"Ожидался статус 400 для архивированного проекта, получен {get_archived_project_response.status_code}"
            assert get_archived_project_response.json().get('error', {}).get('code') == 'ItemInArchive', \
                f"Ожидался код ошибки 'ItemInArchive', получен {get_archived_project_response.json().get('error', {}).get('code')} ({get_archived_project_response.text})"
        else:
            # Если архивация неуспешна (например, 403), убеждаемся, что проект остался неархивированным
            # Используем owner_client для получения актуального состояния
            get_project_after_failed_archive = owner_client.post(**get_project_endpoint(project_id=main_project_2, space_id=main_space))
            assert get_project_after_failed_archive.status_code == 200, f"Ошибка при получении проекта после неуспешной архивации: {get_project_after_failed_archive.text}"
            project_data_after_failed_archive = get_project_after_failed_archive.json()['payload']['project']
            assert project_data_after_failed_archive.get('archivedAt') is None, "Проект был архивирован, хотя ожидалась ошибка."

    with allure.step(
            f'Шаг 3: Попытка разархивировать проект с ролью {client_fixture}, ожидаемый статус={expected_status}'):
        if expected_status == 200:  # Если клиент смог архивировать (owner/manager), он должен смочь и разархивировать
            unarchive_response = client.post(**unarchive_project_endpoint(project_id=main_project_2, space_id=main_space))
            assert unarchive_response.status_code == 200, \
                f"Ожидался статус 200 для разархивации, получен {unarchive_response.status_code})"
            # Проверяем состояние архивации после успешной разархивации
            final_project_data_response = owner_client.post(
                **get_project_endpoint(project_id=main_project_2, space_id=main_space))
            assert final_project_data_response.status_code == 200
            final_project_data = final_project_data_response.json()['payload']['project']
            assert final_project_data.get('archivedAt') is None, "Проект не был разархивирован."
        else:  # Если клиент не смог архивировать (member/guest), ему не должна быть доступна разархивация
            # Для проверки разархивации сначала убедимся, что проект архивирован owner'ом.
            with allure.step(f'Шаг 3.1: В роли owner архивируем проект для проверки разархивации {client_fixture}'):
                owner_archive_response = owner_client.post(
                    **archive_project_endpoint(project_id=main_project_2, space_id=main_space))
                assert owner_archive_response.status_code == 200, f"Не удалось архивировать проект с owner перед тестом разархивации"
                owner_archived_project_data = owner_archive_response.json()['payload']['project']
                assert owner_archived_project_data.get('archivedAt') is not None, "Проект не был архивирован owner-ом."

            # Теперь пытаемся разархивировать проект с текущим клиентом (member/guest)
            with allure.step(
                    f'Шаг 3.2: Попытка разархивировать проект с ролью {client_fixture}, ожидаемый статус={expected_status}'):
                unarchive_response = client.post(
                    **unarchive_project_endpoint(project_id=main_project_2, space_id=main_space))
                assert unarchive_response.status_code == expected_status, \
                    f"Ожидался статус {expected_status} для разархивации, получен {unarchive_response.status_code})"
                assert unarchive_response.json().get('error', {}).get('code') == 'AccessDenied'

            # Проверяем, что проект остался архивированным после неудачной попытки разархивации
            with allure.step(
                    f'Шаг 3.3: Проверка, что проект остался архивированным после неудачной попытки разархивации {client_fixture}'):
                get_project_status_after_failed_unarchive = owner_client.post(
                    **get_project_endpoint(project_id=main_project_2, space_id=main_space))
                assert get_project_status_after_failed_unarchive.status_code == 400, \
                    f"Ожидался статус 400 (ItemInArchive) после неуспешной разархивации, получен {get_project_status_after_failed_unarchive.status_code}"
                assert get_project_status_after_failed_unarchive.json().get('error', {}).get('code') == 'ItemInArchive', \
                    f"Ожидался код ошибки 'ItemInArchive', получен {get_project_status_after_failed_unarchive.json().get('error', {}).get('code')})"
            with allure.step(
                    f'Шаг 3.4 clin up : Разархивация проекта owner\'ом для очистки состояния после теста {client_fixture}'):
                owner_archive_response_final = owner_client.post(
                    **unarchive_project_endpoint(project_id=main_project_2, space_id=main_space))
                assert owner_archive_response_final.status_code == 200, f"Не удалось повторно архивировать проект с owner для очистки"
