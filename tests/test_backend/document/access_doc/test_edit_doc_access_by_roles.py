from datetime import datetime

import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    edit_document_endpoint,
    archive_document_endpoint,
    get_document_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'creator_fixture, editor_fixture, expected_status',
    [
        # Owner создает документ
        ('owner_client', 'owner_client', 200),  # владелец редактирует свой документ
        ('owner_client', 'manager_client', 200),  # владелец создает, менеджер редактирует
        ('owner_client', 'member_client', 200),  # владелец создает, участник редактирует
        ('owner_client', 'guest_client', 403),  # владелец создает, гость редактирует
        # Manager создает документ
        ('manager_client', 'owner_client', 200),  # менеджер создает, владелец редактирует
        ('manager_client', 'manager_client', 200),  # менеджер редактирует свой документ
        ('manager_client', 'member_client', 200),  # менеджер создает, участник редактирует
        ('manager_client', 'guest_client', 403),  # менеджер создает, гость редактирует
        # Member создает документ
        ('member_client', 'owner_client', 200),  # участник создает, владелец редактирует
        ('member_client', 'manager_client', 200),  # участник создает, менеджер редактирует
        ('member_client', 'member_client', 200),  # участник редактирует свой документ
        ('member_client', 'guest_client', 403),  # участник создает, гость редактирует
    ],
    ids=[
        'owner_self_edit',
        'owner_to_manager',
        'owner_to_member',
        'owner_to_guest',
        'manager_to_owner',
        'manager_self_edit',
        'manager_to_member',
        'manager_to_guest',
        'member_to_owner',
        'member_to_manager',
        'member_self_edit',
        'member_to_guest',
    ],
)
@pytest.mark.parametrize(
    'doc_type, doc_container',
    [
        ('Space', 'main_space'),
        ('Project', 'main_project'),
    ],
    ids=['space_doc', 'project_doc'],
)
def test_edit_project_and_space_docs_different_roles(
    request, main_space, creator_fixture, editor_fixture, expected_status, doc_type, doc_container, create_main_documents
):
    editor_client = request.getfixturevalue(editor_fixture)
    container_id = request.getfixturevalue(doc_container)
    creator_role = creator_fixture.replace('_client', '')
    editor_role = editor_fixture.replace('_client', '')
    
    edited_title = f'Edited Doc {datetime.now().strftime("%Y.%m.%d_%H:%M:%S")}'
    
    allure.dynamic.title(f'Редактирование {doc_type}-документа: создание {creator_role}, редактирование {editor_role}')
    
    with allure.step(f'Создание {doc_type}-документа пользователем с ролью {creator_role}'):
        docs = create_main_documents(
            kind=doc_type, 
            kind_id=container_id,
            creator_roles={creator_fixture: creator_role}
        )
        doc_id = docs[0]['id']
    
    # Редактирование документа второй ролью
    with allure.step(f'Редактирование документа пользователем с ролью {editor_role}'):
        edit_response = editor_client.post(
            **edit_document_endpoint(document_id=doc_id, title=edited_title, icon='+1', space_id=main_space)
        )
        assert edit_response.status_code == expected_status, (
            f'Неожиданный статус при редактировании: {edit_response.status_code}, ' f'ожидался: {expected_status}'
        )
        
        if expected_status == 200:
            with allure.step('Проверка видимости изменений документа для всех ролей'):
                clients_to_check = {
                    'owner': request.getfixturevalue('owner_client'),
                    'manager': request.getfixturevalue('manager_client'),
                    'member': request.getfixturevalue('member_client'),
                    'guest': request.getfixturevalue('guest_client'),
                }
                
                for role, client in clients_to_check.items():
                    with allure.step(f'Проверка для роли {role}'):
                        get_response = client.post(
                            **get_document_endpoint(document_id=doc_id, space_id=main_space)
                        )
                        assert get_response.status_code == 200
                        updated_doc = get_response.json()['payload']['document']
                        assert updated_doc['title'] == edited_title



@pytest.mark.parametrize(
    'creator_fixture, editor_fixture, expected_status',
    [
        # Owner's personal documents
        ('owner_client', 'owner_client', 200),  # владелец редактирует свой документ
        ('owner_client', 'manager_client', 403),  # владелец создает, менеджер пытается редактировать
        ('owner_client', 'member_client', 403),  # владелец создает, участник пытается редактировать
        ('owner_client', 'guest_client', 403),  # владелец создает, гость пытается редактировать
        # Manager's personal documents
        ('manager_client', 'owner_client', 403),  # менеджер создает, владелец пытается редактировать
        ('manager_client', 'manager_client', 200),  # менеджер редактирует свой документ
        ('manager_client', 'member_client', 403),  # менеджер создает, участник пытается редактировать
        ('manager_client', 'guest_client', 403),  # менеджер создает, гость пытается редактировать
        # Member's personal documents
        ('member_client', 'owner_client', 403),  # участник создает, владелец пытается редактировать
        ('member_client', 'manager_client', 403),  # участник создает, менеджер пытается редактировать
        ('member_client', 'member_client', 200),  # участник редактирует свой документ
        ('member_client', 'guest_client', 403),  # участник создает, гость пытается редактировать
    ],
    ids=[
        'owner_self_edit_personal',
        'owner_personal_by_manager',
        'owner_personal_by_member',
        'owner_personal_by_guest',
        'manager_personal_by_owner',
        'manager_self_edit_personal',
        'manager_personal_by_member',
        'manager_personal_by_guest',
        'member_personal_by_owner',
        'member_personal_by_manager',
        'member_self_edit_personal',
        'member_personal_by_guest',
    ],
)
def test_edit_personal_doc_different_roles(
    request, main_space, main_personal, creator_fixture, editor_fixture, expected_status
):
    creator_client = request.getfixturevalue(creator_fixture)
    editor_client = request.getfixturevalue(editor_fixture)

    creator_role = creator_fixture.replace('_client', '')
    editor_role = editor_fixture.replace('_client', '')

    document_title = f'{datetime.now().strftime("%Y.%m.%d_%H:%M:%S")} Personal Doc For Editing'
    edited_title = f'Edited {datetime.now().strftime("%Y.%m.%d_%H:%M:%S")}'
    doc_id = None

    allure.dynamic.title(f'Редактирование Personal-документа: создание {creator_role}, редактирование {editor_role}')

    try:
        # Создание персонального документа
        with allure.step(f'Создание Personal-документа пользователем с ролью {creator_role}'):
            create_response = creator_client.post(
                **create_document_endpoint(
                    kind='Member', kind_id=main_personal[creator_role][0], space_id=main_space, title=document_title
                )
            )
            assert create_response.status_code == 200, (
                f'Ошибка при создании документа пользователем {creator_role}: ' f'статус {create_response.status_code}'
            )
            doc_id = create_response.json()['payload']['document']['_id']

        # Редактирование документа
        with allure.step(
            f'Редактирование документа пользователем с ролью {editor_role} (Нельзя редактировать чужие персональные документы)'
        ):
            edit_response = editor_client.post(
                **edit_document_endpoint(document_id=doc_id, title=edited_title, icon='icon_test', space_id=main_space)
            )
            assert edit_response.status_code == expected_status, (
                f'Неожиданный статус при редактировании: {edit_response.status_code}, ' f'ожидался: {expected_status}'
            )

            if expected_status == 200:
                get_response = creator_client.post(**get_document_endpoint(document_id=doc_id, space_id=main_space))
                assert get_response.status_code == 200
                updated_doc = get_response.json()['payload']['document']
                assert updated_doc['title'] == edited_title, (
                    f'Название документа не изменилось. '
                    f'Ожидалось: "{edited_title}", Получено: "{updated_doc["title"]}"'
                )

    finally:
        if doc_id:
            with allure.step('Архивация документа'):
                creator_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))