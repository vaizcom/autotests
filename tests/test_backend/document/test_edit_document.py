import pytest
import allure

from test_backend.data.endpoints.Document.document_endpoints import get_document_endpoint
from tests.test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    edit_document_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_edit_document_success(owner_client, request, kind, kind_id_fixture, temp_space, temp_document):
    allure.dynamic.title(f'Успешное редактирование полей title и icon. {kind}')

    # Редактируем title и icon
    new_title = 'EditedTitle'
    new_icon = 'EditedIcon'
    with allure.step('Edit document'):
        edit_resp = owner_client.post(
            **edit_document_endpoint(
                document_id=temp_document['_id'],
                title=new_title,
                icon=new_icon,
                space_id=temp_space,
            )
        )
        assert edit_resp.status_code == 200
        body = edit_resp.json()
        assert body.get('type') == 'EditDocument'
        updated = body['payload']['document']
        assert updated['_id'] == temp_document['_id']
        assert updated['title'] == new_title
        assert updated['icon'] == new_icon


@pytest.mark.parametrize(
    'fake_id, expected_status',
    [
        ('000000000000000000000000', 400),
        ('', 400),
        (None, 400),
        ('bad_format', 400),
    ],
    ids=['not_found', 'empty', 'null', 'bad_format'],
)
def test_edit_document_invalid_id(owner_client, temp_space, fake_id, expected_status):
    allure.dynamic.title(f'Негативные сценарии: некорректный documentId. id={fake_id}')
    with allure.step('Attempt edit with invalid id'):
        resp = owner_client.post(
            **edit_document_endpoint(
                document_id=fake_id,
                title='X',
                icon='Y',
                space_id=temp_space,
            )
        )
        assert resp.status_code == expected_status
        body = resp.json()
        payload = body.get('payload')
        if payload:
            assert 'document' not in payload
        else:
            assert payload is None


@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_edit_document_forbidden_no_membership(
    owner_client, guest_client, kind, kind_id_fixture, temp_space, temp_document
):
    allure.dynamic.title(
        f'Попытка редактировать документ из чужого space (kind={kind})— должен вернуться MemberDidNotFound'
    )
    # Создаем документ владельцем temp_document
    # Гость пытается редактировать
    with allure.step('Guest edit attempt'):
        resp2 = guest_client.post(
            **edit_document_endpoint(
                document_id=temp_document['_id'],
                title='X',
                icon='Y',
                space_id=temp_space,
            )
        )
        assert resp2.status_code == 400
        body2 = resp2.json()
        assert 'error' in body2
        assert not body2.get('payload')
        assert body2['error']['code'] == 'MemberDidNotFound'


@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_edit_document_overwrite_race_condition(owner_client, kind, kind_id_fixture, temp_space, temp_document):
    allure.dynamic.title(
        f'Два последовательных запроса на редактирование одного документа- проверяем что последнее изменение сохранилось.{kind}'
    )
    # 1) Создаём документ temp_document["_id"]
    # 2) Первый апдейт
    first_title = 'FirstUpdate'
    first_icon = 'IconA'
    with allure.step('Первое редактирование'):
        r1 = owner_client.post(
            **edit_document_endpoint(
                document_id=temp_document['_id'],
                title=first_title,
                icon=first_icon,
                space_id=temp_space,
            )
        )
        assert r1.status_code == 200
        updated1 = r1.json()['payload']['document']
        assert updated1['title'] == first_title
        assert updated1['icon'] == first_icon

    # 3) Второй апдейт
    second_title = 'SecondUpdate'
    second_icon = 'IconB'
    with allure.step('Второе редактирование (перезапись)'):
        r2 = owner_client.post(
            **edit_document_endpoint(
                document_id=temp_document['_id'],
                title=second_title,
                icon=second_icon,
                space_id=temp_space,
            )
        )
        assert r2.status_code == 200
        updated2 = r2.json()['payload']['document']
        assert updated2['title'] == second_title
        assert updated2['icon'] == second_icon

    # 4) Финальная проверка: выгружаем документ и убеждаемся в последних значениях
    with allure.step('Проверка итогового состояния документа'):
        # Предполагаем, что есть endpoint GET /documents/{id}
        get_resp = owner_client.post(**get_document_endpoint(document_id=temp_document['_id'], space_id=temp_space))
        assert get_resp.status_code == 200
        final = get_resp.json()['payload']['document']
        assert final['title'] == second_title
        assert final['icon'] == second_icon


@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'project_id_function'),
        ('Space', 'space_id_function'),
        ('Member', 'member_id_function'),
    ],
    ids=['project', 'space', 'member'],
)
@pytest.mark.parametrize(
    'length, expected_status',
    [
        (2048, 200),  # граница принятия
        (2049, 400),  # превышение максимума
    ],
    ids=['max_allowed', 'exceed_max'],
)
def test_edit_document_title_length(
    owner_client, request, kind, kind_id_fixture, space_id_function, length, expected_status
):
    allure.dynamic.title(f'Проверка граничной валидации длины title: LENGTH = {length} for {kind}')
    kind_id = request.getfixturevalue(kind_id_fixture)

    # Создаём документ
    resp = owner_client.post(
        **create_document_endpoint(
            kind=kind,
            kind_id=kind_id,
            space_id=space_id_function,
            title='Original',
        )
    )
    assert resp.status_code == 200, f'Failed to create document: {resp.text}'
    doc_id = resp.json()['payload']['document']['_id']

    # Формируем title заданной длины
    boundary_title = 'A' * length
    with allure.step(f'Attempt edit with title length {length}'):
        resp2 = owner_client.post(
            **edit_document_endpoint(
                document_id=doc_id,
                title=boundary_title,
                icon='ValidIcon',
                space_id=space_id_function,
            )
        )
        assert resp2.status_code == expected_status, f'Expected {expected_status}, got {resp2.status_code}'
        if expected_status == 400:
            error_code = resp2.json().get('error', {}).get('code')
            assert error_code == 'InvalidForm', f"Expected error code 'InvalidForm', got {error_code}"
