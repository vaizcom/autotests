import pytest
import allure

from tests.test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    get_document_siblings_endpoint,
)

pytestmark = [pytest.mark.backend]


@pytest.mark.parametrize(
    'kind, fixture_name',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_get_document_siblings(owner_client, request, temp_space, kind, fixture_name):
    kind_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Получение сиблингов документа (kind={kind})')

    with allure.step('Создание родительского документа'):
        resp = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title='Parent')
        )
        assert resp.status_code == 200
        parent_id = resp.json()['payload']['document']['_id']

    with allure.step('Создание дочерних документов с разными индексами'):
        titles = ['Sibling A', 'Sibling B', 'Sibling C']
        indices = [0, 1, 2]
        sibling_ids = []

        for title, index in zip(titles, indices):
            resp = owner_client.post(
                **create_document_endpoint(
                    kind=kind,
                    kind_id=kind_id,
                    space_id=temp_space,
                    title=title,
                    parent_document_id=parent_id,
                    index=index,
                )
            )
            assert resp.status_code == 200
            sibling_ids.append(resp.json()['payload']['document']['_id'])

    with allure.step('Запрос сиблингов для среднего документа (index=1)'):
        child_id = sibling_ids[1]
        resp = owner_client.post(**get_document_siblings_endpoint(document_id=child_id, space_id=temp_space))
        assert resp.status_code == 200
        payload = resp.json()['payload']

    with allure.step('Проверка корректности сиблингов'):
        assert payload['prevSibling']['_id'] == sibling_ids[0]
        assert payload['nextSibling']['_id'] == sibling_ids[2]
        assert payload['parents'][0]['_id'] == parent_id
        assert any(node['document']['_id'] == child_id for node in payload['tree'])
