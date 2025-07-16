from datetime import datetime
import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    get_document_siblings_endpoint,
    archive_document_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'creator_fixture, client_fixture, expected_status',
    [
        ('owner_client', 'owner_client', 200),
        ('owner_client', 'manager_client', 200),
        ('owner_client', 'member_client', 200),
        ('owner_client', 'guest_client', 200),
        ('manager_client', 'owner_client', 200),
        ('manager_client', 'manager_client', 200),
        ('manager_client', 'member_client', 200),
        ('manager_client', 'guest_client', 200),
        ('member_client', 'owner_client', 200),
        ('member_client', 'manager_client', 200),
        ('member_client', 'member_client', 200),
        ('member_client', 'guest_client', 200),
    ],
    ids=[
        'owner_self_docs_200',
        'owner_docs_by_manager_403',
        'owner_docs_by_member_403',
        'owner_docs_by_guest_403',
        'manager_docs_by_owner_403',
        'manager_self_docs_200',
        'manager_docs_by_member_403',
        'manager_docs_by_guest_403',
        'member_docs_by_owner_403',
        'member_docs_by_manager_403',
        'member_self_docs_200',
        'member_docs_by_guest_403',
    ]
)
@pytest.mark.parametrize(
    'kind, container_fixture',
    [
        ('Space', 'main_space'),
        ('Project', 'main_project'),
    ],
    ids=['space_doc', 'project_doc']
)
def test_get_project_and_space_siblings_docs_access_by_roles(
    request, main_space, creator_fixture, client_fixture, expected_status, kind, container_fixture
):
    """
    Проверяет доступ к siblings документов при разных комбинациях:
    - Создателя документа
    - Просматривающего пользователя
    - Типа документа (Space/Project)
    
    Проверки:
        1. Создание трёх последовательных документов указанной ролью
        2. Запрос siblings для среднего документа другой ролью
        3. Проверка статуса ответа и корректности данных siblings
    """
    creator = request.getfixturevalue(creator_fixture)
    viewer = request.getfixturevalue(client_fixture)
    creator_role = creator_fixture.replace('_client', '')
    viewer_role = client_fixture.replace('_client', '')
    container_id = request.getfixturevalue(container_fixture)
    
    current_date = datetime.now().strftime('%d.%m_%H:%M:%S')
    
    allure.dynamic.title(
        f'Проверка доступа к siblings {kind}-документа: создатель - {creator_role}, просматривающий - {viewer_role}'
    )
    
    doc_ids = []
    with allure.step(f'Создание трёх {kind}-документов пользователем {creator_role}'):
        for index in range(3):
            title = f'{current_date}_{creator_role}_{kind}_Doc_{index}'
            create_resp = creator.post(
                **create_document_endpoint(
                    kind=kind,
                    kind_id=container_id,
                    space_id=main_space,
                    title=title
                )
            )
            assert create_resp.status_code == 200, (
                f'Ошибка при создании документа {index}: статус {create_resp.status_code}'
            )
            doc_id = create_resp.json()['payload']['document']['_id']
            doc_ids.append(doc_id)
    
    middle_doc_id = doc_ids[1]
    with allure.step(f'Попытка получения siblings для среднего документа пользователем {viewer_role}'):
        siblings_resp = viewer.post(
            **get_document_siblings_endpoint(document_id=middle_doc_id, space_id=main_space)
        )
        assert siblings_resp.status_code == expected_status
        
        if siblings_resp.status_code == 200:
            payload = siblings_resp.json().get('payload', {})
            with allure.step('Проверка корректности данных siblings'):
                # Проверка наличия обязательных полей
                assert 'prevSibling' in payload, 'Отсутствует поле prevSibling'
                assert 'nextSibling' in payload, 'Отсутствует поле nextSibling'
                assert 'tree' in payload, 'Отсутствует поле tree'
                
                # Проверка корректности siblings
                assert payload['prevSibling']['_id'] == doc_ids[0], 'Некорректный левый сосед'
                assert payload['nextSibling']['_id'] == doc_ids[2], 'Некорректный правый сосед'
                
                # Проверка дополнительных полей в siblings
                for sibling in [payload['prevSibling'], payload['nextSibling']]:
                    assert 'title' in sibling, 'Отсутствует поле title в siblings'
                    assert 'kind' in sibling, 'Отсутствует поле kind в siblings'
                    assert sibling['kind'] == kind, f'Некорректный kind в siblings: {sibling["kind"]}, ожидался: {kind}'
    
    with allure.step('Архивация созданных документов'):
        for doc_id in doc_ids:
            archive_resp = creator.post(
                **archive_document_endpoint(space_id=main_space, document_id=doc_id)
            )
            assert archive_resp.status_code == 200


@pytest.mark.parametrize(
    'creator_fixture, client_fixture, expected_status',
    [
        # Owner's personal documents
        ('owner_client', 'owner_client', 200),  # владелец смотрит свои документы
        ('owner_client', 'manager_client', 403),  # менеджер пытается смотреть документы владельца
        ('owner_client', 'member_client', 403),  # участник пытается смотреть документы владельца
        ('owner_client', 'guest_client', 403),  # гость пытается смотреть документы владельца
        # Manager's personal documents
        ('manager_client', 'owner_client', 403),  # владелец пытается смотреть документы менеджера
        ('manager_client', 'manager_client', 200),  # менеджер смотрит свои документы
        ('manager_client', 'member_client', 403),  # участник пытается смотреть документы менеджера
        ('manager_client', 'guest_client', 403),  # гость пытается смотреть документы менеджера
        # Member's personal documents
        ('member_client', 'owner_client', 403),  # владелец пытается смотреть документы участника
        ('member_client', 'manager_client', 403),  # менеджер пытается смотреть документы участника
        ('member_client', 'member_client', 200),  # участник смотрит свои документы
        ('member_client', 'guest_client', 403),  # гость пытается смотреть документы участника
        # Guest's personal documents
        ('guest_client', 'owner_client', 403),  # владелец пытается смотреть документы гостя
        ('guest_client', 'manager_client', 403),  # менеджер пытается смотреть документы гостя
        ('guest_client', 'member_client', 403),  # участник пытается смотреть документы гостя
        ('guest_client', 'guest_client', 200),  # гость смотрит свои документы
    ],
    ids=[
        'owner_self_docs_200',
        'owner_docs_by_manager_403',
        'owner_docs_by_member_403',
        'owner_docs_by_guest_403',
        'manager_docs_by_owner_403',
        'manager_self_docs_200',
        'manager_docs_by_member_403',
        'manager_docs_by_guest_403',
        'member_docs_by_owner_403',
        'member_docs_by_manager_403',
        'member_self_docs_200',
        'member_docs_by_guest_403',
        'guest_docs_by_owner_403',
        'guest_docs_by_manager_403',
        'guest_docs_by_member_403',
        'guest_self_docs_200',
    ]
)
def test_get_personal_siblings_docs_access_by_roles(
        request, main_space, main_personal, creator_fixture, client_fixture, expected_status
):
    """
    Проверяет доступ к siblings персональных (Member) документов при разных комбинациях:
    - Создателя документа
    - Просматривающего пользователя

    Проверки:
        1. Создание трёх последовательных документов указанной ролью
        2. Запрос siblings для среднего документа другой ролью
        3. Проверка статуса ответа и корректности данных siblings

    Особенность: к персональным документам имеет доступ только их владелец
    """
    creator = request.getfixturevalue(creator_fixture)
    viewer = request.getfixturevalue(client_fixture)
    creator_role = creator_fixture.replace('_client', '')
    viewer_role = client_fixture.replace('_client', '')

    current_date = datetime.now().strftime('%d.%m_%H:%M:%S')

    allure.dynamic.title(
        f'Проверка доступа к siblings персонального документа: создатель - {creator_role}, просматривающий - {viewer_role}'
    )

    doc_ids = []
    with allure.step(f'Создание трёх персональных документов пользователем {creator_role}'):
        for index in range(3):
            title = f'{current_date}_{creator_role}_Member_Doc_{index}'
            create_resp = creator.post(
                **create_document_endpoint(
                    kind='Member',
                    kind_id=main_personal[creator_role][0],
                    space_id=main_space,
                    title=title
                )
            )
            assert create_resp.status_code == 200, (
                f'Ошибка при создании документа {index}: статус {create_resp.status_code}'
            )
            doc_id = create_resp.json()['payload']['document']['_id']
            doc_ids.append(doc_id)

    middle_doc_id = doc_ids[1]
    with allure.step(f'Попытка получения siblings для среднего документа пользователем {viewer_role}'):
        siblings_resp = viewer.post(
            **get_document_siblings_endpoint(document_id=middle_doc_id, space_id=main_space)
        )
        assert siblings_resp.status_code == expected_status

        if siblings_resp.status_code == 200:
            payload = siblings_resp.json().get('payload', {})
            with allure.step('Проверка корректности данных siblings'):
                # Проверка наличия обязательных полей
                assert 'prevSibling' in payload, 'Отсутствует поле prevSibling'
                assert 'nextSibling' in payload, 'Отсутствует поле nextSibling'
                assert 'tree' in payload, 'Отсутствует поле tree'

                # Проверка корректности siblings
                assert payload['prevSibling']['_id'] == doc_ids[0], 'Некорректный левый сосед'
                assert payload['nextSibling']['_id'] == doc_ids[2], 'Некорректный правый сосед'

                # Проверка дополнительных полей в siblings
                for sibling in [payload['prevSibling'], payload['nextSibling']]:
                    assert 'title' in sibling, 'Отсутствует поле title в siblings'
                    assert 'kind' in sibling, 'Отсутствует поле kind в siblings'
                    assert sibling[
                               'kind'] == 'Member', f'Некорректный kind в siblings: {sibling["kind"]}, ожидался: Member'

    with allure.step('Архивация созданных документов'):
        for doc_id in doc_ids:
            archive_resp = creator.post(
                **archive_document_endpoint(space_id=main_space, document_id=doc_id)
            )
            assert archive_resp.status_code == 200