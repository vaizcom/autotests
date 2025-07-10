from datetime import datetime

import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    duplicate_document_endpoint,
    archive_document_endpoint,
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
@pytest.mark.parametrize(
    'doc_type, doc_container',
    [
        ('Project', 'main_project'),
        ('Space', 'main_space'),
    ],
    ids=['project_doc', 'space_doc']
)
def test_duplicate_project_and_space_docs_access(
    request, 
    main_space, 
    client_fixture, 
    expected_status, 
    doc_type, 
    doc_container
):
    api_client = request.getfixturevalue(client_fixture)
    container_id = request.getfixturevalue(doc_container)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} Doc For Duplication'
    doc_id = None
    doc_copy_id = None
    
    allure.dynamic.title(f'Дублирование {doc_type}-документа для роли {role}')
    
    try:
        with allure.step(f'Создание {doc_type}-документа'):
            create_resp = api_client.post(
                **create_document_endpoint(
                    kind=doc_type, 
                    kind_id=container_id, 
                    space_id=main_space, 
                    title=title
                )
            )
            if create_resp.status_code != 200:
                with allure.step(f'Не удалось создать документ, статус {create_resp.status_code} — пропуск дублирования'):
                    assert (
                        expected_status == 403
                    ), f'Невозможно протестировать дублирование без документа (статус создания {create_resp.status_code})'
                return
            
            doc_id = create_resp.json()['payload']['document']['_id']
            original_title = create_resp.json()['payload']['document']['title']
        
        with allure.step(f'Дублирование документа пользователем с ролью {role}'):
            dup_resp = api_client.post(**duplicate_document_endpoint(document_id=doc_id, space_id=main_space))
            if dup_resp.status_code != expected_status:
                allure.attach(dup_resp.text, name='Response Body', attachment_type=allure.attachment_type.JSON)
            assert dup_resp.status_code == expected_status, f'Ожидали {expected_status}, получили {dup_resp.status_code}'
            
            if expected_status == 200:
                doc_copy = dup_resp.json()['payload']['document']
                doc_copy_id = doc_copy['_id']
                copy_title = doc_copy['title']
                
                with allure.step('Проверка названия дублированного документа'):
                    expected_title = f'{original_title} (copy)'
                    assert copy_title == expected_title, (
                        f'Неверный формат названия копии. '
                        f'Ожидалось: "{expected_title}", Получено: "{copy_title}"'
                    )
    
    finally:
        # Cleanup
        if doc_id:
            with allure.step('Архивация исходного документа (cleanup)'):
                archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
                assert archive_resp.status_code == 200
                
        if doc_copy_id:
            with allure.step('Архивация Copy-документа (cleanup)'):
                archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_copy_id))
                assert archive_resp.status_code == 200


@pytest.mark.parametrize(
    'creator_fixture, duplicator_fixture, expected_status',
    [
        ('owner_client', 'member_client', 200),  # владелец создает, участник дублирует
        ('manager_client', 'guest_client', 403),  # менеджер создает, гость дублирует
        ('member_client', 'manager_client', 200),  # участник создает, менеджер дублирует
        ('owner_client', 'guest_client', 403),  # владелец создает, гость дублирует
        ('manager_client', 'member_client', 200),  # менеджер создает, участник дублирует
    ],

    ids=['owner_to_member', 'manager_to_guest', 'member_to_manager',
         'owner_to_guest', 'manager_to_member']

)
@pytest.mark.parametrize(
    'doc_type, doc_container',
    [
        ('Project', 'main_project'),
        ('Space', 'main_space'),
    ],
    ids=['project_doc', 'space_doc']
)
def test_duplicate_project_and_space_docs_different_roles(
        request,
        main_space,
        creator_fixture,
        duplicator_fixture,
        expected_status,
        doc_type,
        doc_container
):
    # Получаем клиентов для создания и дублирования
    creator_client = request.getfixturevalue(creator_fixture)
    duplicator_client = request.getfixturevalue(duplicator_fixture)

    container_id = request.getfixturevalue(doc_container)
    creator_role = creator_fixture.replace('_client', '')
    duplicator_role = duplicator_fixture.replace('_client', '')

    document_title = f'{datetime.now().strftime("%Y.%m.%d_%H:%M:%S")} Doc For Duplication'
    doc_id = None
    doc_copy_id = None

    allure.dynamic.title(
        f'Дублирование {doc_type}-документа: создание {creator_role}, дублирование {duplicator_role}'
    )

    try:
        # Создание документа первой ролью
        with allure.step(f'Создание {doc_type}-документа пользователем с ролью {creator_role}'):
            create_response = creator_client.post(
                **create_document_endpoint(
                    kind=doc_type,
                    kind_id=container_id,
                    space_id=main_space,
                    title=document_title
                )
            )

            # Проверяем что документ создался
            assert create_response.status_code == 200, (
                f'Ошибка при создании документа пользователем {creator_role}: '
                f'статус {create_response.status_code}'
            )

            doc_id = create_response.json()['payload']['document']['_id']
            original_title = create_response.json()['payload']['document']['title']

        # Дублирование документа второй ролью
        with allure.step(f'Дублирование документа пользователем с ролью {duplicator_role}'):
            duplicate_response = duplicator_client.post(
                **duplicate_document_endpoint(document_id=doc_id, space_id=main_space)
            )

            if duplicate_response.status_code != expected_status:
                allure.attach(
                    duplicate_response.text,
                    name='Response Body',
                    attachment_type=allure.attachment_type.JSON
                )

            assert duplicate_response.status_code == expected_status, (
                f'Неожиданный статус при дублировании: {duplicate_response.status_code}, '
                f'ожидался: {expected_status}'
            )

            # Проверяем результат успешного дублирования
            if expected_status == 200:
                doc_copy = duplicate_response.json()['payload']['document']
                doc_copy_id = doc_copy['_id']

                with allure.step('Проверка названия дублированного документа'):
                    expected_title = f'{original_title} (copy)'
                    assert doc_copy['title'] == expected_title, (
                        f'Неверный формат названия копии. '
                        f'Ожидалось: "{expected_title}", Получено: "{doc_copy["title"]}"'
                    )

    finally:
        # Очистка тестовых данных
        if doc_id:
            with allure.step('Архивация исходного документа'):
                creator_client.post(
                    **archive_document_endpoint(space_id=main_space, document_id=doc_id)
                )

        if doc_copy_id:
            with allure.step('Архивация копии документа'):
                duplicator_client.post(
                    **archive_document_endpoint(space_id=main_space, document_id=doc_copy_id)
                )


@pytest.mark.parametrize(
    'client_fixture',
    ['owner_client', 'manager_client', 'member_client', 'guest_client'],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_duplicate_personal_doc_access(request, main_space, main_personal, client_fixture):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    title = f'{current_date} Personal Doc For Duplication'
    doc_id = None
    doc_copy_id = None
    
    allure.dynamic.title(f'Дублирование Personal-документа пользователем с ролью {role}')
    
    try:
        with allure.step(f'Создание Personal-документа для пользователя с ролью {role}'):
            create_resp = api_client.post(
                **create_document_endpoint(
                    kind='Member', 
                    kind_id=main_personal[role][0], 
                    space_id=main_space, 
                    title=title
                )
            )
            assert create_resp.status_code == 200, 'Создание Personal-документа должно быть доступно всем ролям'
            
            doc_id = create_resp.json()['payload']['document']['_id']
            original_title = create_resp.json()['payload']['document']['title']
        
        with allure.step(f'Дублирование документа пользователем с ролью {role}'):
            dup_resp = api_client.post(**duplicate_document_endpoint(document_id=doc_id, space_id=main_space))
            assert dup_resp.status_code == 200, 'Дублирование Personal-документа должно быть доступно всем ролям'
            
            doc_copy = dup_resp.json()['payload']['document']
            doc_copy_id = doc_copy['_id']
            copy_title = doc_copy['title']
            
            with allure.step('Проверка названия дублированного документа'):
                expected_title = f'{original_title} (copy)'
                assert copy_title == expected_title, (
                    f'Неверный формат названия копии. '
                    f'Ожидалось: "{expected_title}", Получено: "{copy_title}"'
                )
    
    finally:
        # Cleanup
        if doc_id:
            with allure.step('Архивация исходного документа (cleanup)'):
                archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))
                assert archive_resp.status_code == 200
                
        if doc_copy_id:
            with allure.step('Архивация Copy-документа (cleanup)'):
                archive_resp = api_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_copy_id))
                assert archive_resp.status_code == 200

@pytest.mark.parametrize(
    'creator_fixture, duplicator_fixture, expected_status',
    [
        ('member_client', 'owner_client', 403),     # владелец пытается дублировать чужой personal-документ
        ('owner_client', 'member_client', 403),     # участник пытается дублировать чужой personal-документ
    ],
    ids=['owner_other', 'member_other']
)
def test_duplicate_personal_doc_different_roles(
        request,
        main_space,
        main_personal,
        creator_fixture,
        duplicator_fixture,
        expected_status
):
    creator_client = request.getfixturevalue(creator_fixture)
    duplicator_client = request.getfixturevalue(duplicator_fixture)

    creator_role = creator_fixture.replace('_client', '')
    duplicator_role = duplicator_fixture.replace('_client', '')

    document_title = f'{datetime.now().strftime("%Y.%m.%d_%H:%M:%S")} Personal Doc For Duplication'
    doc_id = None
    doc_copy_id = None

    allure.dynamic.title(
        f'Дублирование Personal-документа: создание {creator_role}, дублирование {duplicator_role}'
    )

    try:
        # Создание персонального документа
        with allure.step(f'Создание Personal-документа пользователем с ролью {creator_role}'):
            create_response = creator_client.post(
                **create_document_endpoint(
                    kind='Member',
                    kind_id=main_personal[creator_role][0],
                    space_id=main_space,
                    title=document_title
                )
            )

            assert create_response.status_code == 200, (
                f'Ошибка при создании документа пользователем {creator_role}: '
                f'статус {create_response.status_code}'
            )

            doc_id = create_response.json()['payload']['document']['_id']
            original_title = create_response.json()['payload']['document']['title']

        # Дублирование документа
        with allure.step(f'Дублирование документа пользователем с ролью {duplicator_role}'):
            duplicate_response = duplicator_client.post(
                **duplicate_document_endpoint(document_id=doc_id, space_id=main_space)
            )

            if duplicate_response.status_code != expected_status:
                allure.attach(
                    duplicate_response.text,
                    name='Response Body',
                    attachment_type=allure.attachment_type.JSON
                )

            assert duplicate_response.status_code == expected_status, (
                f'Неожиданный статус при дублировании: {duplicate_response.status_code}, '
                f'ожидался: {expected_status}'
            )

            if expected_status == 200:
                doc_copy = duplicate_response.json()['payload']['document']
                doc_copy_id = doc_copy['_id']

                with allure.step('Проверка названия дублированного документа'):
                    expected_title = f'{original_title} (copy)'
                    assert doc_copy['title'] == expected_title

    finally:
        # Очистка тестовых данных
        if doc_id:
            with allure.step('Архивация исходного документа'):
                creator_client.post(
                    **archive_document_endpoint(space_id=main_space, document_id=doc_id)
                )

        if doc_copy_id:
            with allure.step('Архивация копии документа'):
                duplicator_client.post(
                    **archive_document_endpoint(space_id=main_space, document_id=doc_copy_id)
                )