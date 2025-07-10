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
def test_duplicate_doc_access_by_roles(
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