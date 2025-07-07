from datetime import datetime

import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    archive_document_endpoint,
    edit_document_endpoint,
    get_document_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 403),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_edit_space_doc_access_by_roles(request, main_space, client_fixture, expected_status):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} {role} Space Doc For Editing'

    allure.dynamic.title(f'Редактирование Space-документа для роли {role}')

    with allure.step(f'{role} создаёт Space-документ для редактирования'):
        create_resp = api_client.post(
            **create_document_endpoint(
                kind='Space',
                kind_id=main_space,
                space_id=main_space,
                title=title,
            )
        )

        if create_resp.status_code != 200:
            with allure.step(f'Не удалось создать документ, статус {create_resp.status_code} — пропуск редактирования'):
                assert expected_status == 403
            return

        doc_id = create_resp.json()['payload']['document']['_id']

    with allure.step(f'{role} пытается отредактировать документ {title}'):
        edit_resp = api_client.post(
            **edit_document_endpoint(
                document_id=doc_id, title=f'Edited {current_date} {role}', icon='icon_test', space_id=main_space
            )
        )
        assert edit_resp.status_code == expected_status

        if edit_resp.status_code == 200:
            get_resp = api_client.post(**get_document_endpoint(document_id=doc_id, space_id=main_space))
            assert get_resp.status_code == 200
            updated_title = get_resp.json()['payload']['document']['title']
            assert updated_title == f'Edited {current_date} {role}', 'Название документа не изменилось'

    with allure.step(f'Архивация документа {title}'):
        archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
        assert archive_resp.status_code == 200
