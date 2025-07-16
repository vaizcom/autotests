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
    'creator_fixture, duplicator_fixture, expected_status',
    [
        # Owner создает документ
        ('owner_client', 'owner_client', 200),  # владелец дублирует свой документ
        ('owner_client', 'manager_client', 200),  # владелец создает, менеджер дублирует
        ('owner_client', 'member_client', 200),  # владелец создает, участник дублирует
        ('owner_client', 'guest_client', 403),  # владелец создает, гость дублирует
        # Manager создает документ
        ('manager_client', 'owner_client', 200),  # менеджер создает, владелец дублирует
        ('manager_client', 'manager_client', 200),  # менеджер дублирует свой документ
        ('manager_client', 'member_client', 200),  # менеджер создает, участник дублирует
        ('manager_client', 'guest_client', 403),  # менеджер создает, гость дублирует
        # Member создает документ
        ('member_client', 'owner_client', 200),  # участник создает, владелец дублирует
        ('member_client', 'manager_client', 200),  # участник создает, менеджер дублирует
        ('member_client', 'member_client', 200),  # участник дублирует свой документ
        ('member_client', 'guest_client', 403),  # участник создает, гость дублирует
    ],
    ids=[
        # Owner создает
        'owner_self_duplicate',
        'owner_to_manager',
        'owner_to_member',
        'owner_to_guest',
        # Manager создает
        'manager_to_owner',
        'manager_self_duplicate',
        'manager_to_member',
        'manager_to_guest',
        # Member создает
        'member_to_owner',
        'member_to_manager',
        'member_self_duplicate',
        'member_to_guest',
    ],
)
@pytest.mark.parametrize(
    'doc_type, doc_container',
    [
        ('Project', 'main_project'),
        ('Space', 'main_space'),
    ],
    ids=['project_doc', 'space_doc'],
)
def test_duplicate_project_and_space_docs_different_roles(
    request, main_space, creator_fixture, duplicator_fixture, expected_status, doc_type, doc_container
):
    """
    Тест проверяет дублирование документов разными ролями и типами документов. Тест проверяет, что документы могут быть 
    созданы одной ролью и продублированы другой в соответствии с ожидаемыми условиями, указанными в параметризации.
    """
    # Получаем клиентов для создания и дублирования
    creator_client = request.getfixturevalue(creator_fixture)
    duplicator_client = request.getfixturevalue(duplicator_fixture)

    container_id = request.getfixturevalue(doc_container)
    creator_role = creator_fixture.replace('_client', '')
    duplicator_role = duplicator_fixture.replace('_client', '')

    document_title = f'{datetime.now().strftime("%Y.%m.%d_%H:%M:%S")} Doc For Duplication'
    doc_id = None
    doc_copy_id = None

    allure.dynamic.title(f'Дублирование {doc_type}-документа: создание {creator_role}, дублирование {duplicator_role}')

    try:
        # Создание документа первой ролью
        with allure.step(f'Создание {doc_type}-документа пользователем с ролью {creator_role}'):
            create_response = creator_client.post(
                **create_document_endpoint(
                    kind=doc_type, kind_id=container_id, space_id=main_space, title=document_title
                )
            )

            # Проверяем что документ создался
            assert create_response.status_code == 200, (
                f'Ошибка при создании документа пользователем {creator_role}: ' f'статус {create_response.status_code}'
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
                    duplicate_response.text, name='Response Body', attachment_type=allure.attachment_type.JSON
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
                creator_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))

        if doc_copy_id:
            with allure.step('Архивация копии документа'):
                duplicator_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_copy_id))


@pytest.mark.parametrize(
    'creator_fixture, duplicator_fixture, expected_status',
    [
        # Owner's personal documents
        ('owner_client', 'owner_client', 200),  # владелец дублирует свой personal-документ
        ('owner_client', 'manager_client', 403),  # владелец создает, менеджер пытается дублировать
        ('owner_client', 'member_client', 403),  # владелец создает, участник пытается дублировать
        ('owner_client', 'guest_client', 403),  # владелец создает, гость пытается дублировать
        # Manager's personal documents
        ('manager_client', 'owner_client', 403),  # менеджер создает, владелец пытается дублировать
        ('manager_client', 'manager_client', 200),  # менеджер дублирует свой personal-документ
        ('manager_client', 'member_client', 403),  # менеджер создает, участник пытается дублировать
        ('manager_client', 'guest_client', 403),  # менеджер создает, гость пытается дублировать
        # Member's personal documents
        ('member_client', 'owner_client', 403),  # участник создает, владелец пытается дублировать
        ('member_client', 'manager_client', 403),  # участник создает, менеджер пытается дублировать
        ('member_client', 'member_client', 200),  # участник дублирует свой personal-документ
        ('member_client', 'guest_client', 403),  # участник создает, гость пытается дублировать
        # Guest's personal documents
        ('guest_client', 'owner_client', 403),  # гость создает, владелец пытается дублировать
        ('guest_client', 'manager_client', 403),  # гость создает, менеджер пытается дублировать
        ('guest_client', 'member_client', 403),  # гость создает, участник пытается дублировать
        ('guest_client', 'guest_client', 200),  # гость дублирует свой personal-документ
    ],
    ids=[
        # Owner's personal docs
        'owner_self_personal',
        'owner_personal_by_manager',
        'owner_personal_by_member',
        'owner_personal_by_guest',
        # Manager's personal docs
        'manager_personal_by_owner',
        'manager_self_personal',
        'manager_personal_by_member',
        'manager_personal_by_guest',
        # Member's personal docs
        'member_personal_by_owner',
        'member_personal_by_manager',
        'member_self_personal',
        'member_personal_by_guest',
        # Guest's personal docs
        'guest_personal_by_owner',
        'guest_personal_by_manager',
        'guest_personal_by_member',
        'guest_self_personal',
    ],
)
def test_duplicate_personal_doc_different_roles(
    request, main_space, main_personal, creator_fixture, duplicator_fixture, expected_status
):
    creator_client = request.getfixturevalue(creator_fixture)
    duplicator_client = request.getfixturevalue(duplicator_fixture)

    creator_role = creator_fixture.replace('_client', '')
    duplicator_role = duplicator_fixture.replace('_client', '')

    document_title = f'{datetime.now().strftime("%Y.%m.%d_%H:%M:%S")} Personal Doc For Duplication'
    doc_id = None
    doc_copy_id = None

    allure.dynamic.title(f'Дублирование Personal-документа: создание {creator_role}, дублирование {duplicator_role}')

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
            original_title = create_response.json()['payload']['document']['title']

        # Дублирование документа
        with allure.step(
            f'Дублирование документа пользователем с ролью {duplicator_role} (Нельзя дублировать чужие персональные документы)'
        ):
            duplicate_response = duplicator_client.post(
                **duplicate_document_endpoint(document_id=doc_id, space_id=main_space)
            )

            if duplicate_response.status_code != expected_status:
                allure.attach(
                    duplicate_response.text, name='Response Body', attachment_type=allure.attachment_type.JSON
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
                creator_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_id))

        if doc_copy_id:
            with allure.step('Архивация копии документа'):
                duplicator_client.post(**archive_document_endpoint(space_id=main_space, document_id=doc_copy_id))
