import pytest
import allure

from test_backend.data.endpoints.Document.document_endpoints import (
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
    allure.dynamic.title(f'Проверка отсутствия siblins и родителей для одного корневого документа (kind={kind})')

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


@allure.feature('Document Siblings')
@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'project_id_function'),
        ('Space', 'space_id_function'),
        ('Member', 'member_id_function'),
    ],
    ids=['project', 'space', 'member'],
)
def test_root_level_siblings(owner_client, request, kind, kind_id_fixture, space_id_function):
    """
    Проверяем сиблинги для нескольких корневых документов (без parent_document_id).
    """
    allure.dynamic.title(f'Проверяем siblins для нескольких корневых документов (kind={kind})')
    kind_id = request.getfixturevalue(kind_id_fixture)
    titles = ['Root A', 'Root B', 'Root C']
    doc_ids = []

    with allure.step('Создаем корневые документы'):
        for title in titles:
            resp = owner_client.post(
                **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=space_id_function, title=title)
            )
            assert resp.status_code == 200, f'Не удалось создать документ {title}: {resp.text}'
            doc_ids.append(resp.json()['payload']['document']['_id'])

    with allure.step('Проверка сиблингов для первого документа'):
        resp1 = owner_client.post(**get_document_siblings_endpoint(document_id=doc_ids[0], space_id=space_id_function))
        assert resp1.status_code == 200
        p1 = resp1.json()['payload']
        assert 'prevSibling' not in p1 or p1.get('prevSibling') is None
        assert p1['nextSibling']['_id'] == doc_ids[1]
        assert p1['parents'] == []

    with allure.step('Проверка сиблингов для среднего документа'):
        resp2 = owner_client.post(**get_document_siblings_endpoint(document_id=doc_ids[1], space_id=space_id_function))
        assert resp2.status_code == 200
        p2 = resp2.json()['payload']
        assert p2['prevSibling']['_id'] == doc_ids[0]
        assert p2['nextSibling']['_id'] == doc_ids[2]
        assert p2['parents'] == []

    with allure.step('Проверка сиблингов для последнего документа'):
        resp3 = owner_client.post(**get_document_siblings_endpoint(document_id=doc_ids[2], space_id=space_id_function))
        assert resp3.status_code == 200
        p3 = resp3.json()['payload']
        assert p3['prevSibling']['_id'] == doc_ids[1]
        assert 'nextSibling' not in p3 or p3.get('nextSibling') is None
        assert p3['parents'] == []


@allure.feature('Document Siblings')
@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'project_id_function'),
        ('Space', 'space_id_function'),
        ('Member', 'member_id_function'),
    ],
    ids=['project', 'space', 'member'],
)
def test_deeply_nested_parents(owner_client, request, kind, kind_id_fixture, space_id_function):
    """
    Глубокая вложенность: проверяем цепочку parents.
    """
    allure.dynamic.title(
        f'Проверяем глубокую вложенность для Grandchild = [root_id, parent_id, child_id] (kind={kind})'
    )
    kind_id = request.getfixturevalue(kind_id_fixture)

    with allure.step('Создаём цепочку вложенности'):
        # Level 1
        r = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=space_id_function, title='Root')
        )
        assert r.status_code == 200
        root_id = r.json()['payload']['document']['_id']
        # Level 2
        p = owner_client.post(
            **create_document_endpoint(
                kind=kind, kind_id=kind_id, space_id=space_id_function, title='Parent', parent_document_id=root_id
            )
        )
        assert p.status_code == 200
        parent_id = p.json()['payload']['document']['_id']
        # Level 3
        c = owner_client.post(
            **create_document_endpoint(
                kind=kind, kind_id=kind_id, space_id=space_id_function, title='Child', parent_document_id=parent_id
            )
        )
        assert c.status_code == 200
        child_id = c.json()['payload']['document']['_id']
        # Level 4
        g = owner_client.post(
            **create_document_endpoint(
                kind=kind, kind_id=kind_id, space_id=space_id_function, title='Grandchild', parent_document_id=child_id
            )
        )
        assert g.status_code == 200
        grand_id = g.json()['payload']['document']['_id']

    with allure.step('Проверяем цепочку parents'):
        resp = owner_client.post(**get_document_siblings_endpoint(document_id=grand_id, space_id=space_id_function))
        assert resp.status_code == 200
        parents_list = resp.json()['payload']['parents']
        ids = [node['_id'] for node in parents_list]
        assert ids == [root_id, parent_id, child_id], f'Неверный порядок parents: {ids}'

    with allure.step('Проверяем tree содержит только Grandchild'):
        tree = resp.json()['payload']['tree']
        assert len(tree) == 1, f'Ожидался один элемент в tree, но получено {len(tree)}'
        assert (
            tree[0]['document']['_id'] == grand_id
        ), f"tree должен содержать только Grandchild, но найден {tree[0]['document']['_id']}"


@allure.feature('Document Siblings')
@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'project_id_function'),
        ('Space', 'space_id_function'),
        ('Member', 'member_id_function'),
    ],
    ids=['project', 'space', 'member'],
)
def test_single_child_siblings(owner_client, request, kind, kind_id_fixture, space_id_function):
    """
    Единственный ребёнок: нет prevSibling/nextSibling, parents содержит родителя.
    """
    allure.dynamic.title(f'Проверяем siblins для единственного SoloChild (kind={kind})')
    kind_id = request.getfixturevalue(kind_id_fixture)

    with allure.step('Создаём родителя'):
        r = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=space_id_function, title='OnlyParent')
        )
        assert r.status_code == 200
        parent_id = r.json()['payload']['document']['_id']

    with allure.step('Создаём единственного ребёнка'):
        c = owner_client.post(
            **create_document_endpoint(
                kind=kind, kind_id=kind_id, space_id=space_id_function, title='SoloChild', parent_document_id=parent_id
            )
        )
        assert c.status_code == 200
        child_id = c.json()['payload']['document']['_id']

    with allure.step('Проверяем сиблинги единственного ребёнка'):
        resp = owner_client.post(**get_document_siblings_endpoint(document_id=child_id, space_id=space_id_function))
        assert resp.status_code == 200
        payload = resp.json()['payload']
        assert 'prevSibling' not in payload or payload.get('prevSibling') is None
        assert 'nextSibling' not in payload or payload.get('nextSibling') is None
        assert payload['parents'][0]['_id'] == parent_id


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
    allure.dynamic.title(f'Проверяем siblins для нескольктих Child (kind={kind})')

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


@pytest.mark.parametrize(
    'fake_id, expected_status',
    [
        ('000000000000000000000000', 400),  # valid ObjectId format but not found
        ('', 400),  # empty string invalid format
        ('123', 400),  # too short, invalid format
        ('notAnObjectId1234567890', 400),  # non-hex characters
        (None, 400),  # null value
    ],
    ids=['not_found', 'empty', 'short', 'non_hex', 'null'],
)
def test_invalid_document_id(owner_client, space_id_function, fake_id, expected_status):
    """
    Негативные сценарии: разные варианты некорректного document_id.
    """
    allure.dynamic.title(f'Негативный: некорректный document_id={fake_id}')
    with allure.step('Запрос сиблингов с некорректным ID'):
        # Подготовка параметров
        params = {'document_id': fake_id, 'space_id': space_id_function}
        # Выполняем запрос
        resp = owner_client.post(**get_document_siblings_endpoint(**params))
        # Проверяем код ответа
        assert (
            resp.status_code == expected_status
        ), f'Ожидался статус {expected_status} для fake_id={fake_id}, но получен {resp.status_code}'
        # Проверяем отсутствие полезной нагрузки
        body = resp.json()
        assert not body.get('payload'), 'payload не должен присутствовать для некорректного ID'


@pytest.mark.parametrize(
    'kind, kind_id_fixture',
    [
        ('Project', 'project_id_function'),
        ('Space', 'space_id_function'),
        ('Member', 'member_id_function'),
    ],
    ids=['project', 'space', 'member'],
)
def test_get_document_siblings_foreign_space(
    owner_client, guest_client, request, kind, kind_id_fixture, space_id_function
):
    allure.dynamic.title(f'Негативный сценарий: гостевой пользователь не может получить siblings (kind={kind})')
    kind_id = request.getfixturevalue(kind_id_fixture)

    with allure.step('Создаём документ владельцем'):
        create_resp = owner_client.post(
            **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=space_id_function, title='UnauthorizedDoc')
        )
        assert create_resp.status_code == 200, f'Не удалось создать документ: {create_resp.text}'
        doc_id = create_resp.json()['payload']['document']['_id']

    with allure.step('Пытаемся получить сиблинги как гость'):
        resp = guest_client.post(**get_document_siblings_endpoint(document_id=doc_id, space_id=space_id_function))
        assert resp.status_code == 403, f'Ожидался 403, но получен {resp.status_code}'

    with allure.step('Проверяем отсутствие payload в ответе'):
        assert not resp.json().get('payload'), 'У гостя не должно быть payload'
