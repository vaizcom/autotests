import random
from datetime import datetime

import allure
import pytest

from test_backend.data.endpoints.Document.document_endpoints import (
    get_documents_endpoint, create_document_endpoint, archive_document_endpoint,
)

pytestmark = [pytest.mark.backend]

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
def test_get_space_docs_list_access_by_roles(request, main_space, client_fixture, expected_status):
    api_client = request.getfixturevalue(client_fixture)
    role = client_fixture.replace('_client', '')
    current_date = datetime.now().strftime('%d.%m_%H:%M:%S')
    title = f"{current_date}_{role}_Space Doc For List Check"

    allure.dynamic.title(f"Получение списка Space-документов для роли {role}")
    random_client = request.getfixturevalue(random.choice(['owner_client', 'manager_client', 'member_client']))

    with allure.step(f"random_client({random_client}) создаёт Space-документ для проверки списка {title}"):

        create_resp = random_client.post(
            **create_document_endpoint(
                kind='Space',
                kind_id=main_space,
                space_id=main_space,
                title=title
            )
        )

        if create_resp.status_code != 200:
            with allure.step(f"Не удалось создать документ, статус {create_resp.status_code} — пропуск проверки списка"):
                assert expected_status == 403
            return

        doc_id = create_resp.json()["payload"]["document"]["_id"]

    with allure.step(f"{role} пытается получить список документов пространства"):
        list_resp = api_client.post(
            **get_documents_endpoint(kind='Space', kind_id=main_space, space_id=main_space)
        )
        assert list_resp.status_code == expected_status
        if list_resp.status_code == 200:
            docs = list_resp.json()["payload"].get("documents", [])
            assert isinstance(docs, list), "Документы должны быть списком"
            with allure.step("Проверка наличия созданного документа в списке"):
                doc_ids = [doc["_id"] for doc in docs]
                assert doc_id in doc_ids, "Созданный документ не найден в списке"

    with allure.step(f"Архивация созданного документа {title}"):
        archive_resp = random_client.post(
            **archive_document_endpoint(space_id=main_space, document_id=doc_id)
        )
        assert archive_resp.status_code == 200
