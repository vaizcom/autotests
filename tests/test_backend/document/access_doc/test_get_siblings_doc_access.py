from datetime import datetime

import allure
import pytest

from conftest import member_client
from test_backend.data.endpoints.Document.document_endpoints import (
    create_document_endpoint, get_document_siblings_endpoint, archive_document_endpoint,
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
def test_get_space_doc_siblings_access_by_roles(request, main_space, client_fixture, expected_status):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%d.%m_%H:%M:%S')

    allure.dynamic.title(f"Получение соседей Space-документа для роли {role}")

    doc_ids = []
    with allure.step(f"{role} создаёт три Space-документа для проверки соседей"):
        for index in range(3):
            title = f"{current_date}_{role}_Sibling Test Doc {index}"
            create_resp = api_client.post(
                **create_document_endpoint(
                    kind='Space',
                    kind_id=main_space,
                    space_id=main_space,
                    title=title
                )
            )
            if create_resp.status_code != 200:
                with allure.step(f"Не удалось создать документ {index}, статус {create_resp.status_code}"):
                    assert expected_status == 403
                return
            doc_id = create_resp.json()["payload"]["document"]["_id"]
            doc_ids.append(doc_id)

    middle_doc_id = doc_ids[1]

    with allure.step(f"{role} пытается получить соседей для среднего документа"):
        siblings_resp = api_client.post(
            **get_document_siblings_endpoint(document_id=middle_doc_id, space_id=main_space)
        )
        assert siblings_resp.status_code == expected_status

        if siblings_resp.status_code == 200:
            payload = siblings_resp.json().get("payload", {})
            with allure.step("Проверка наличия левого и правого соседа"):
                assert "prevSibling" in payload, "Нет prevSibling в ответе"
                assert "nextSibling" in payload, "Нет nextSibling в ответе"
                assert payload["prevSibling"]["_id"] == doc_ids[0], "Некорректный левый сосед"
                assert payload["nextSibling"]["_id"] == doc_ids[2], "Некорректный правый сосед"

    with allure.step("Архивация созданных документов"):
        for doc_id in doc_ids:
            archive_resp = api_client.post(
                **archive_document_endpoint(space_id=main_space, document_id=doc_id)
            )
            assert archive_resp.status_code == 200


@pytest.mark.parametrize(
    'client_fixture, expected_status',
    [
        ('owner_client', 200),
        ('manager_client', 200),
        ('member_client', 200),
        ('guest_client', 200),
    ],
    ids=['owner', 'manager', 'member', 'guest'],
)
def test_get_space_doc_siblings_view_only_access(request, main_space, member_client, client_fixture, expected_status):
    role = client_fixture.replace('_client', '')
    api_client = request.getfixturevalue(client_fixture)
    current_date = datetime.now().strftime('%d.%m_%H:%M:%S')

    allure.dynamic.title(f"Просмотр соседей Space-документа для роли {role} (без создания)")

    with allure.step("Создание документов в роли member для теста просмотра siblings"):
        doc_ids = []
        for index in range(3):
            title = f"{current_date}_member_create_Sibling Test Doc {index}"
            create_resp = member_client.post(
                **create_document_endpoint(
                    kind='Space',
                    kind_id=main_space,
                    space_id=main_space,
                    title=title
                )
            )
            assert create_resp.status_code == 200
            doc_id = create_resp.json()["payload"]["document"]["_id"]
            doc_ids.append(doc_id)

    middle_doc_id = doc_ids[1]

    with allure.step(f"{role} пытается получить соседей для среднего документа"):
        siblings_resp = api_client.post(
            **get_document_siblings_endpoint(document_id=middle_doc_id, space_id=main_space)
        )
        assert siblings_resp.status_code == expected_status

        if siblings_resp.status_code == 200:
            payload = siblings_resp.json().get("payload", {})
            with allure.step("Проверка наличия левого и правого соседа"):
                assert "prevSibling" in payload, "Нет prevSibling в ответе"
                assert "nextSibling" in payload, "Нет nextSibling в ответе"
                assert payload["prevSibling"]["_id"] == doc_ids[0], "Некорректный левый сосед"
                assert payload["nextSibling"]["_id"] == doc_ids[2], "Некорректный правый сосед"

    with allure.step("Архивация созданных документов"):
        for doc_id in doc_ids:
            archive_resp = member_client.post(
                **archive_document_endpoint(space_id=main_space, document_id=doc_id)
            )
            assert archive_resp.status_code == 200
