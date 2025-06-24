import time

import pytest
import allure
import random

from config.generators import generate_slug
from test_backend.data.endpoints.Project.project_endpoints import create_project_endpoint
from tests.test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint,
    get_documents_endpoint,
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
def test_get_documents(owner_client, temp_space, request, kind, fixture_name):
    allure.dynamic.title(f'Получение документов — кейс: kind={kind}')

    kind_id = request.getfixturevalue(fixture_name)
    count = random.randint(1, 5)
    titles = [f'Random doc для kind={kind} #{i}' for i in range(count)]

    with allure.step(f'Создание {count} (Random[1,5]) документов с kind={kind}'):
        for title in titles:
            response = owner_client.post(
                **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title=title)
            )
            assert response.status_code == 200

    with allure.step(f'Получение списка документов по kind={kind}'):
        response = owner_client.post(**get_documents_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space))
        assert response.status_code == 200
        docs = response.json()['payload']['documents']

    with allure.step('Проверка, что все созданные документы присутствуют в списке'):
        doc_titles = [doc['title'] for doc in docs]
        for title in titles:
            assert title in doc_titles, f'Документ "{title}" не найден в списке'


@pytest.mark.parametrize(
    'kind, kind_id, space_id, expected_status, case_id',
    [
        ('Project', 'nonexistent-id', 'valid_space_id', 400, 'invalid kindId'),
        ('WrongKind', 'valid_project_id', 'valid_space_id', 400, 'invalid kind'),
        (None, 'valid_project_id', 'valid_space_id', 400, 'missing kind'),
        ('Project', None, 'valid_space_id', 400, 'missing kindId'),
    ],
    ids=['invalid kindId', 'invalid kind', 'missing kind', 'missing kindId'],
)
def test_get_documents_invalid_inputs(
    owner_client, temp_space, temp_project, kind, kind_id, space_id, expected_status, case_id
):
    allure.dynamic.title(f'Негативный кейс: {case_id}')

    if kind_id == 'valid_project_id':
        kind_id = temp_project

    with allure.step(f'Отправка запроса и проверка статуса {expected_status}, проверка ошибки "InvalidForm"'):
        response = owner_client.post(**get_documents_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space))
        assert (
            response.status_code == expected_status
        ), f'Ожидался статус {expected_status}, но получен {response.status_code}'
        assert response.json()['error']['code'] == 'InvalidForm'


@pytest.mark.parametrize(
    'kind, fixture_name',
    [
        ('Project', 'project_id_module'),
        ('Space', 'space_id_module'),
        ('Member', 'member_id_module'),
    ],
    ids=['project', 'space', 'member'],
)
def test_get_documents_empty_list(owner_client, space_id_module, request, kind, fixture_name):
    kind_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Пустой результат при отсутствии документов (kind={kind})')

    with allure.step(f'Запрос документов без предварительного создания (kind={kind}, kindId={kind_id})'):
        response = owner_client.post(**get_documents_endpoint(kind=kind, kind_id=kind_id, space_id=space_id_module))

    with allure.step('Проверка успешного ответа и пустого списка'):
        assert response.status_code == 200
        payload = response.json().get('payload', {})
        documents = payload.get('documents')
        assert isinstance(documents, list), f'Ожидался список, но получили: {type(documents)}'
        assert len(documents) == 0, f'Ожидался пустой список документов, но получено: {documents}'


@allure.title('Project: изолированность документов по kindId проектов')
def test_get_documents_isolation_by_kind_id(owner_client, temp_space, temp_project):
    other_project = owner_client.post(
        **create_project_endpoint(
            name='Other project',
            slug=generate_slug(),
            space_id=temp_space,
            color='green',
            icon='cursor',
            description='test',
        )
    ).json()['payload']['project']['_id']

    with allure.step('Создание документа для первого проекта'):
        response1 = owner_client.post(
            **create_document_endpoint(kind='Project', kind_id=temp_project, space_id=temp_space, title='Doc 1')
        )
        assert response1.status_code == 200
        doc1_id = response1.json()['payload']['document']['_id']

    with allure.step('Создание документа для второго проекта'):
        response2 = owner_client.post(
            **create_document_endpoint(kind='Project', kind_id=other_project, space_id=temp_space, title='Doc 2')
        )
        assert response2.status_code == 200
        doc2_id = response2.json()['payload']['document']['_id']

    with allure.step('Получение документов только для первого проекта'):
        response = owner_client.post(
            **get_documents_endpoint(kind='Project', kind_id=temp_project, space_id=temp_space)
        )
        assert response.status_code == 200
        docs = response.json()['payload']['documents']
        doc_ids = [doc['_id'] for doc in docs]

    with allure.step('Проверка, что вернулся только нужный документ'):
        assert doc1_id in doc_ids
        assert doc2_id not in doc_ids


def test_cross_kind_isolation(owner_client, temp_space, temp_project, temp_member):
    allure.dynamic.title('Документы разных kind не попадают в результаты других kind')
    with allure.step('Создание документа с kind=Member'):
        response = owner_client.post(
            **create_document_endpoint(kind='Member', kind_id=temp_member, space_id=temp_space, title='Member doc')
        )
        assert response.status_code == 200

    with allure.step('Запрос документов по kind=Project, Документ Member doc не попал в результат'):
        response = owner_client.post(
            **get_documents_endpoint(kind='Project', kind_id=temp_project, space_id=temp_space)
        )
        assert response.status_code == 200
        titles = [doc['title'] for doc in response.json()['payload']['documents']]
        assert 'Member doc' not in titles, 'Документ от другого kind попал в результат'

    with allure.step('Запрос документов по kind=Space, Документ Member doc не попал в результат'):
        response = owner_client.post(**get_documents_endpoint(kind='Space', kind_id=temp_space, space_id=temp_space))
        assert response.status_code == 200
        titles = [doc['title'] for doc in response.json()['payload']['documents']]
        assert 'Member doc' not in titles, 'Документ от другого kind попал в результат'


@pytest.mark.parametrize(
    'kind, fixture_name',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_foreign_space_access_denied(owner_client, request, kind, fixture_name, foreign_space):
    kind_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Запрос документов с kind={kind}, но с чужим spaceId')

    with allure.step(f'Попытка запроса с kindId от {kind}, но с чужим spaceId'):
        response = owner_client.post(**get_documents_endpoint(kind=kind, kind_id=kind_id, space_id=foreign_space))

    with allure.step('Проверка, что доступ запрещён'):
        assert response.status_code == 403, f'Ожидался статус 403, но получен {response.status_code}'
        error = response.json().get('error', {})
        assert (
            error.get('code') == 'AccessDenied'
        ), f"Ожидался код ошибки 'AccessDenied', но получен: {error.get('code')}"


@pytest.mark.parametrize(
    'kind, wrong_fixture, case_title',
    [
        ('Project', 'temp_member', 'kind=Project с kindId от Member'),
        ('Member', 'temp_project', 'kind=Member с kindId от Project'),
        ('Space', 'temp_member', 'kind=Space с kindId от Member'),
    ],
    ids=['project-wrong-id', 'member-wrong-id', 'space-wrong-id'],
)
def test_get_documents_mismatched_kind_and_id(owner_client, temp_space, request, kind, wrong_fixture, case_title):
    kind_id = request.getfixturevalue(wrong_fixture)
    allure.dynamic.title(f'Несоответствие kind и kindId — {case_title}')

    with allure.step(f'Отправка запроса с kind={kind} и kindId от {wrong_fixture}'):
        response = owner_client.post(**get_documents_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space))

    with allure.step('Ожидаем ошибку 403'):
        assert response.status_code == 403
        error_code = response.json().get('error', {}).get('code')
        assert error_code == 'AccessDenied', f'Неожиданный код ошибки: {error_code}'


@pytest.mark.parametrize(
    'kind, fixture_name',
    [
        ('Project', 'temp_project'),
        ('Space', 'temp_space'),
        ('Member', 'temp_member'),
    ],
    ids=['project', 'space', 'member'],
)
def test_documents_sorted_by_created_at(owner_client, request, temp_space, kind, fixture_name):
    kind_id = request.getfixturevalue(fixture_name)
    allure.dynamic.title(f'Сортировка документов по createdAt (kind={kind})')

    with allure.step('Создание документов с небольшими задержками'):
        titles = ['Doc A', 'Doc B', 'Doc C']
        for title in titles:
            response = owner_client.post(
                **create_document_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space, title=title)
            )
            assert response.status_code == 200
            time.sleep(1)

    with allure.step('Получение документов'):
        response = owner_client.post(**get_documents_endpoint(kind=kind, kind_id=kind_id, space_id=temp_space))
        assert response.status_code == 200
        documents = response.json()['payload']['documents']
        created_ats = [doc['createdAt'] for doc in documents]

    with allure.step('Проверка сортировки по createdAt'):
        assert created_ats == sorted(created_ats), 'Документы не отсортированы по createdAt'
