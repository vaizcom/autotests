import pytest
import allure

from tests.test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    edit_document_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'project_id_function'),
        ('Space', 'space_id_function'),
        ('Member', 'member_id_function'),
    ],
    ids=['project', 'space', 'member'],
)
def test_edit_document_success(owner_client, request, kind, kind_id_fixture, space_id_function):
    """
    Успешное редактирование полей title и icon.
    """
    allure.dynamic.title(f'EditDocument success for {kind}')
    kind_id = request.getfixturevalue(kind_id_fixture)

    # Создаем документ
    with allure.step('Create document'):
        resp = owner_client.post(
            **create_document_endpoint(
                kind=kind,
                kind_id=kind_id,
                space_id=space_id_function,
                title='Original',
            )
        )
        assert resp.status_code == 200
        doc = resp.json()['payload']['document']
        doc_id = doc['_id']

    # Редактируем title и icon
    new_title = 'EditedTitle'
    new_icon = 'EditedIcon'
    with allure.step('Edit document'):
        edit_resp = owner_client.post(
            **edit_document_endpoint(
                document_id=doc_id,
                title=new_title,
                icon=new_icon,
                space_id=space_id_function,
            )
        )
        assert edit_resp.status_code == 200
        body = edit_resp.json()
        assert body.get('type') == 'EditDocument'
        updated = body['payload']['document']
        assert updated['_id'] == doc_id
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
def test_edit_document_invalid_id(owner_client, space_id_function, fake_id, expected_status):
    """
    Негативные сценарии: некорректный documentId.
    """
    allure.dynamic.title(f'EditDocument invalid id={fake_id}')
    with allure.step('Attempt edit with invalid id'):
        resp = owner_client.post(
            **edit_document_endpoint(
                document_id=fake_id,
                title='X',
                icon='Y',
                space_id=space_id_function,
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
        ('Project', 'project_id_function'),
        ('Space', 'space_id_function'),
        ('Member', 'member_id_function'),
    ],
    ids=['project', 'space', 'member'],
)
def test_edit_document_unauthorized(owner_client, guest_client, request, kind, kind_id_fixture, space_id_function):
    """
    Гость не может редактировать документ.
    """
    allure.dynamic.title(f'EditDocument unauthorized for {kind}')
    kind_id = request.getfixturevalue(kind_id_fixture)

    # Создаем документ владельцем
    resp = owner_client.post(
        **create_document_endpoint(
            kind=kind,
            kind_id=kind_id,
            space_id=space_id_function,
            title='Original',
        )
    )
    assert resp.status_code == 200
    doc_id = resp.json()['payload']['document']['_id']

    # Гость пытается редактировать
    with allure.step('Guest edit attempt'):
        resp2 = guest_client.post(
            **edit_document_endpoint(
                document_id=doc_id,
                title='X',
                icon='Y',
                space_id=space_id_function,
            )
        )
        assert resp2.status_code == 400
        body2 = resp2.json()
        assert 'error' in body2
        assert not body2.get('payload')


# Дополнительный негативный тест: превышение максимальной длины title


@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'project_id_function'),
        ('Space', 'space_id_function'),
        ('Member', 'member_id_function'),
    ],
    ids=['project', 'space', 'member'],
)
def test_edit_document_title_too_long(owner_client, request, kind, kind_id_fixture, space_id_function):
    """
    Негативный сценарий: title превышает MAX_DOC_NAME_LENGTH (2048).
    """
    allure.dynamic.title(f'EditDocument title too long for {kind}')
    kind_id = request.getfixturevalue(kind_id_fixture)

    # Создаем документ владельцем
    resp = owner_client.post(
        **create_document_endpoint(
            kind=kind,
            kind_id=kind_id,
            space_id=space_id_function,
            title='Original',
        )
    )
    assert resp.status_code == 200
    doc_id = resp.json()['payload']['document']['_id']

    # Формируем слишком длинный title
    long_title = 'A' * (2048 + 1)
    with allure.step('Attempt edit with too long title'):
        resp2 = owner_client.post(
            **edit_document_endpoint(
                document_id=doc_id,
                title=long_title,
                icon='ValidIcon',
                space_id=space_id_function,
            )
        )
        # Ожидаем 400 и код ошибки FieldTooLong
        assert resp2.status_code == 400, f'Expected 400 for too long title, got {resp2.status_code}'
        error_code = resp2.json().get('error', {}).get('code')
        assert error_code == 'InvalidForm', f"Expected error code 'InvalidForm', got {error_code}"
