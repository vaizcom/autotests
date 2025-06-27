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
        ('Project', 'project_id_module'),
        ('Space', 'space_id_module'),
        ('Member', 'member_id_module'),
    ],
    ids=['project', 'space', 'member'],
)
def test_get_document_parent_siblings(owner_client, request, space_id_module, kind, kind_id_fixture):
    """Тест проверки siblins и родителей для родительского документа"""
    kind_id = request.getfixturevalue(kind_id_fixture)
    space_id = space_id_module
    allure.dynamic.title(f'Проверка siblins родителя (kind={kind})')

    # Создаем родительский документ
    resp = owner_client.post(**create_document_endpoint(kind=kind, kind_id=kind_id, space_id=space_id, title='Parent'))
    assert resp.status_code == 200, f'Ожидался статус 200, но получен {resp.status_code}'
    parent_id = resp.json()['payload']['document']['_id']

    # Запрос siblins для родительского документа
    with allure.step('Запрос siblins для родительского документа'):
        parent_resp = owner_client.post(**get_document_siblings_endpoint(document_id=parent_id, space_id=space_id))
        assert parent_resp.status_code == 200, f'Ожидался статус 200, но получен {parent_resp.status_code}'
        data = parent_resp.json()
        assert (
            data.get('type') == 'GetDocumentSiblings'
        ), f"Ожидался type 'GetDocumentSiblings', но получен {data.get('type')}"
    parent_payload = parent_resp.json()['payload']

    # Проверка отсутствия prevSibling и nextSibling
    with allure.step('Проверка отсутствия prevSibling и nextSibling'):
        assert 'prevSibling' not in parent_payload, 'prevSibling не должен присутствовать в ответе'
        assert 'nextSibling' not in parent_payload, 'nextSibling не должен присутствовать в ответе'

    # Проверка пустого списка parents
    with allure.step('Проверка пустого списка parents'):
        assert parent_payload['parents'] == [], 'parents для родителя должен быть пустым'

    # Проверка tree содержит только родителя
    with allure.step('Проверка tree содержит только родителя'):
        assert len(parent_payload['tree']) == 1, 'В tree должен быть только parent'
        assert parent_payload['tree'][0]['document']['_id'] == parent_id, 'В tree должен быть только parent'


@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'project_id_module'),
        ('Space', 'space_id_module'),
        ('Member', 'member_id_module'),
    ],
    ids=['project', 'space', 'member'],
)
def test_get_document_siblings(owner_client, request, space_id_module, kind, kind_id_fixture):
    kind_id = request.getfixturevalue(kind_id_fixture)
    space_id = space_id_module
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
        with allure.step('Проверка кода ответа при запросе сиблингов'):
            assert resp.status_code == 200, f'Ожидался статус 200, но получен {resp.status_code}'
        with allure.step('Проверка поля type в ответе'):
            assert (
                resp.json().get('type') == 'GetDocumentSiblings'
            ), f"Ожидался type 'GetDocumentSiblings', но получен {resp.json().get('type')}"

        payload = resp.json()['payload']

    with allure.step('Проверка корректности prev/nextSibling и parents'):
        assert payload['prevSibling']['_id'] == child_ids[0], 'prevSibling некорректен'
        assert payload['nextSibling']['_id'] == child_ids[2], 'nextSibling некорректен'
        assert payload['parents'][0]['_id'] == parent_id, 'parents некорректен'

    # Проверка сиблингов первого документа
    target_first = child_ids[0]
    with allure.step('Проверка nextSibling для первого документа и отсутствие prevSibling'):
        first_resp = owner_client.post(**get_document_siblings_endpoint(document_id=target_first, space_id=space_id))
        assert first_resp.status_code == 200
        first_data = first_resp.json()['payload']
        assert (
            'prevSibling' not in first_data or first_data.get('prevSibling') is None
        ), 'prevSibling для первого документа должен отсутствовать'
        assert first_data['nextSibling']['_id'] == child_ids[1], 'nextSibling для первого документа некорректен'

    # Проверка сиблингов для последнего документа
    target_last = child_ids[-1]
    with allure.step('Проверка prevSibling для последнего документа и отсутствие nextSibling'):
        last_resp = owner_client.post(**get_document_siblings_endpoint(document_id=target_last, space_id=space_id))
        assert last_resp.status_code == 200
        last_data = last_resp.json()['payload']
        assert last_data['prevSibling']['_id'] == child_ids[-2], 'prevSibling должен указывать на предыдущий элемент'
        assert (
            'nextSibling' not in last_data or last_data.get('nextSibling') is None
        ), 'nextSibling для последнего документа должен отсутствовать'

    with allure.step('Проверка наличия обязательных ключей в payload'):
        assert 'tree' in payload, 'В ответе отсутствует поле tree'
        assert 'parents' in payload, 'В ответе отсутствует поле parents'
        assert 'prevSibling' in payload, 'В ответе отсутствует поле prevSibling'
        assert 'nextSibling' in payload, 'В ответе отсутствует поле nextSibling'

    with allure.step('Проверка структуры tree и полей document'):
        for node in payload['tree']:
            assert 'document' in node, 'В узле дерева отсутствует поле document'
            for attr in ('id', 'lft', 'rgt'):
                assert attr in node, f'В узле дерева отсутствует поле {attr}'
            doc = node['document']
            expected_fields = ['_id', 'title', 'kind', 'kindId', 'map']
            for field in expected_fields:
                assert field in doc, f'В документе отсутствует поле {field}'

    with allure.step('Проверка состава tree'):
        tree_ids = [node['document']['_id'] for node in payload['tree']]
        assert tree_ids == [target_id], f'В tree должен быть только запрошенный документ, но получено: {tree_ids}'
