import pytest
import allure

from tests.test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    get_ydocument_endpoint,
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
def test_get_ydocument_success(owner_client, request, kind, kind_id_fixture, temp_space):
    allure.dynamic.title(f'Позитивный сценарий: успешный экспорт Y-Doc для документа. {kind}')
    kind_id = request.getfixturevalue(kind_id_fixture)

    with allure.step('Создаем документ'):
        resp = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title='TestYDoc')
        )
        assert resp.status_code == 200, f'Не удалось создать документ: {resp.text}'
        doc_id = resp.json()['payload']['document']['_id']

    with allure.step('Запрашиваем Y-Doc без till_commit_id'):
        endpoint = get_ydocument_endpoint(document_id=doc_id, space_id=temp_space)
        resp2 = owner_client.post(**endpoint)
        assert resp2.status_code == 200, f'Ожидался 200, получен {resp2.status_code}'
        body = resp2.json()
        payload = body.get('payload', {})
        assert 'yDoc' in payload, 'В payload должен быть ключ yDoc'
        assert isinstance(payload['yDoc'], list), 'yDoc должен быть массивом'

    with allure.step('Запрашиваем Y-Doc с till_commit_id, если есть commits'):
        commits = payload.get('commits') or []
        if commits:
            till = commits[-1]['_id']
            endpoint2 = get_ydocument_endpoint(document_id=doc_id, space_id=temp_space, till_commit_id=till)
            resp3 = owner_client.get(**endpoint2)
            assert resp3.status_code == 200, f'Ожидался 200, получен {resp3.status_code}'
            body3 = resp3.json()
            payload3 = body3.get('payload', {})
            assert isinstance(payload3.get('yDoc'), list), 'yDoc должен быть массивом'


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
def test_get_ydocument_invalid_id(owner_client, temp_space, fake_id, expected_status):
    """
    Негативный сценарий: разные некорректные document_id.
    """
    allure.dynamic.title(f'Негативный экспорт Y-Doc для document_id={fake_id}')
    with allure.step('Выполняем запрос с некорректным document_id'):
        endpoint = get_ydocument_endpoint(document_id=fake_id, space_id=temp_space)
        resp = owner_client.post(**endpoint)
        assert resp.status_code == expected_status, f'Ожидался {expected_status}, получен {resp.status_code}'
        body = resp.json()
        payload = body.get('payload')
        if payload:
            assert 'yDoc' not in payload, 'yDoc не должен присутствовать в payload'
        else:
            assert payload is None, 'payload не должен присутствовать'


@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_get_ydocument_foreign_space(owner_client, guest_client, request, kind, kind_id_fixture, temp_space):
    """ """
    allure.dynamic.title(
        f'Попытка экспортировать Y-Doc из чужого space(kind={kind})— должен вернуться SpaceIdNotSpecified'
    )
    kind_id = request.getfixturevalue(kind_id_fixture)

    with allure.step('Создаем документ владельцем'):
        resp = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title='GuestYDoc')
        )
        assert resp.status_code == 200, f'Не удалось создать документ: {resp.text}'
        doc_id = resp.json()['payload']['document']['_id']

    with allure.step('Пытаемся экспортировать от гостя'):
        endpoint = get_ydocument_endpoint(document_id=doc_id, space_id=temp_space)
        resp2 = guest_client.post(**endpoint)
        assert resp2.status_code == 400, f'Ожидался 400 получен {resp2.status_code}'
        assert resp2.json()['error']['code'] == 'SpaceIdNotSpecified'
        body2 = resp2.json()
        payload2 = body2.get('payload')
        if payload2:
            assert 'yDoc' not in payload2, 'Гость не должен получить yDoc'
        else:
            assert payload2 is None, 'payload не должен присутствовать'
