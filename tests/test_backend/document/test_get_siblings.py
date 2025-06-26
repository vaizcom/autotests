import pytest
import allure

from tests.test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    get_document_siblings_endpoint,
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
def test_get_document_siblings(owner_client, request, temp_space, kind, kind_id_fixture):
    kind_id = request.getfixturevalue(kind_id_fixture)
    space_id = temp_space
    allure.dynamic.title(f'Получение сиблингов документа (kind={kind})')

    with allure.step('Создание родительского документа'):
        resp = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=space_id, title='Parent')
        )
        assert resp.status_code == 200
        parent_id = resp.json()['payload']['document']['_id']

    with allure.step('Создание дочерних документов'):
        titles = ['Child A', 'Child B', 'Child C']
        child_ids = []

        for title in titles:
            resp = owner_client.post(
                **create_document_endpoint(
                    kind=kind,
                    kind_id=kind_id,
                    space_id=space_id,
                    title=title,
                    parent_document_id=parent_id,
                )
            )
            assert resp.status_code == 200
            child_ids.append(resp.json()['payload']['document']['_id'])

    with allure.step('Запрос сиблингов для среднего дочернего документа'):
        target_id = child_ids[1]
        resp = owner_client.post(**get_document_siblings_endpoint(document_id=target_id, space_id=space_id))
        assert resp.status_code == 200
        payload = resp.json()['payload']

    with allure.step('Проверка наличия обязательных ключей в payload'):
        assert 'tree' in payload, 'В ответе отсутствует поле tree'
        assert 'parents' in payload, 'В ответе отсутствует поле parents'
        assert 'prevSibling' in payload, 'В ответе отсутствует поле prevSibling'
        assert 'nextSibling' in payload, 'В ответе отсутствует поле nextSibling'

    with allure.step('Проверка корректности prev/nextSibling и parents'):
        assert payload['prevSibling']['_id'] == child_ids[0], 'prevSibling некорректен'
        assert payload['nextSibling']['_id'] == child_ids[2], 'nextSibling некорректен'
        assert payload['parents'][0]['_id'] == parent_id, 'parents некорректен'

    with allure.step('Проверка структуры tree и полей document'):
        for node in payload['tree']:
            assert 'document' in node, 'В узле дерева отсутствует поле document'
            doc = node['document']
            expected_fields = ['_id', 'title', 'kind', 'kindId', 'map']
            for field in expected_fields:
                assert field in doc, f'В документе отсутствует поле {field}'

    with allure.step('Проверка состава tree'):
        tree_ids = [node['document']['_id'] for node in payload['tree']]
        assert tree_ids == [target_id], f'В tree должен быть только запрошенный документ, но получено: {tree_ids}'

    with allure.step('Проверка сиблингов родительского документа'):
        resp = owner_client.post(**get_document_siblings_endpoint(document_id=parent_id, space_id=space_id))
        assert resp.status_code == 200
        parent_payload = resp.json()['payload']
        assert parent_payload.get('prevSibling') is None, 'prevSibling для родителя должен быть None'
        assert parent_payload.get('nextSibling') is None, 'nextSibling для родителя должен быть None'
        assert parent_payload['parents'] == [], 'parents для родителя должен быть пустым'
        assert parent_payload['tree'][0]['document']['_id'] == parent_id, 'В tree должен быть только parent'
