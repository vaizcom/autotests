import pytest
import allure
from tests.test_backend.data.endpoints.Document.document_endpoints import get_document_endpoint

pytestmark = [pytest.mark.backend]


@allure.title('Проверка доступа к документам: пользователь без доступа (foreign_client)')
def test_document_access_denied_for_foreign_client(request, foreign_client, main_space):
    """
    Проверяет, что пользователь foreign_client без доступа к Space получает ошибку.
    """
    with allure.step('Отправка запроса для получения доступа к документам'):
        response = foreign_client.post(**get_document_endpoint(document_id=main_space, space_id=main_space))

    with allure.step("Проверка, что запрос отклонён (ожидается 400 и код ошибки 'NotFound')"):
        assert response.status_code == 400, f'Ожидался статус 400, получен {response.status_code}'
        error = response.json().get('error', {})
        assert error.get('code') == 'NotFound', f"Ожидался код ошибки 'NotFound', получен {error.get('code')}"


@allure.title(
    'Проверка доступа space_client к основному документу и отсутствия доступа к проектному документу и персональному документу'
)
def test_space_client_document_access(
    space_client_memb, main_space, main_space_doc, main_project_doc, main_personal_doc
):
    """
    Проверяем, что space_client имеет доступ к main_space_doc и не имеет доступа к main_personal_doc и main_project_doc.

    """
    with allure.step('Проверка доступа к основному документу MAIN_SPACE_DOC_ID'):
        response_space = space_client_memb.post(
            **get_document_endpoint(document_id=main_space_doc, space_id=main_space)
        )
        assert response_space.status_code == 200, 'Доступ к MAIN_SPACE_DOC_ID должен быть разрешён'

    with allure.step('Проверка отсутствия доступа к проектному документу MAIN_PROJECT_DOC_ID'):
        response_project = space_client_memb.post(
            **get_document_endpoint(document_id=main_project_doc, space_id=main_space)
        )
        assert response_project.status_code == 403, 'Доступ к MAIN_PROJECT_DOC_ID должен быть запрещён'

    with allure.step('Проверка отсутствия доступа к персональному документу MAIN_PERSONAL_DOC_ID'):
        response_personal = space_client_memb.post(
            **get_document_endpoint(document_id=main_personal_doc, space_id=main_space)
        )
        assert response_personal.status_code == 403, 'Доступ к MAIN_PERSONAL_DOC_ID должен быть запрещён'


@allure.title(
    'Проверка доступа project_client к основному документу, проектному документу и отсутствия доступа к персональному документу'
)
def test_project_client_document_access(
    project_client, main_space, main_space_doc, main_project_doc, main_personal_doc
):
    """
    Проверяем, что project_client имеет доступ к main_space_doc и main_project_doc, но не имеет доступа к main_personal_doc.
    """

    with allure.step('Проверка доступа project_client к основному документу MAIN_SPACE_DOC_ID'):
        response_space = project_client.post(**get_document_endpoint(document_id=main_space_doc, space_id=main_space))
        assert response_space.status_code == 200, 'Доступ к MAIN_SPACE_DOC_ID должен быть разрешён'

    with allure.step('Проверка доступа project_client к проектному документу MAIN_PROJECT_DOC_ID'):
        response_project = project_client.post(
            **get_document_endpoint(document_id=main_project_doc, space_id=main_space)
        )
        assert response_project.status_code == 200, 'Доступ к MAIN_PROJECT_DOC_ID должен быть разрешён'

    with allure.step('Проверка отсутствия доступа project_client к персональному документу MAIN_PERSONAL_DOC_ID'):
        response_personal = project_client.post(
            **get_document_endpoint(document_id=main_personal_doc, space_id=main_space)
        )
        assert response_personal.status_code == 403, 'Доступ к MAIN_PERSONAL_DOC_ID должен быть запрещён'


@allure.title('Проверка доступа owner_client к документам пространства, проекта и персональному документу')
def test_owner_client_document_access(owner_client, main_space, main_space_doc, main_project_doc, main_personal_doc):
    """
    Проверяем, что owner_client имеет доступ к main_space_doc и main_project_doc,
    но не имеет доступа к main_personal_doc.
    """
    with allure.step('Проверка доступа owner_client к основному документу MAIN_SPACE_DOC_ID'):
        response_space = owner_client.post(**get_document_endpoint(document_id=main_space_doc, space_id=main_space))
        assert response_space.status_code == 200, 'Доступ к MAIN_SPACE_DOC_ID должен быть разрешён'

    with allure.step('Проверка доступа owner_client к проектному документу MAIN_PROJECT_DOC_ID'):
        response_project = owner_client.post(**get_document_endpoint(document_id=main_project_doc, space_id=main_space))
        assert response_project.status_code == 200, 'Доступ к MAIN_PROJECT_DOC_ID должен быть разрешён'

    with allure.step('Проверка отсутствия доступа owner_client к персональному документу MAIN_PERSONAL_DOC_ID'):
        response_personal = owner_client.post(
            **get_document_endpoint(document_id=main_personal_doc, space_id=main_space)
        )
        assert response_personal.status_code == 403, 'Доступ к MAIN_PERSONAL_DOC_ID должен быть запрещён'


@allure.title('Проверка доступа с некорректным ID документа')
@pytest.mark.parametrize(
    'document_id, space_id, expected_status, expected_error_code',
    [
        ('invalid-id-123', 'valid-space-id', 400, 'InvalidForm'),
        ('valid-document-id', 'invalid-space-id-456', 400, 'InvalidForm'),
        ('invalid-id-789', 'invalid-space-id', 400, 'InvalidForm'),
    ],
    ids=['invalid document_id', 'invalid space_id', 'invalid both'],
)
def test_access_with_invalid_ids(owner_client, document_id, space_id, expected_status, expected_error_code):
    """
    Проверяет, что запросы с некорректными document_id или space_id вызывают ошибку.
    """
    with allure.step(f'Попытка получить доступ к документу {document_id} в пространстве {space_id}'):
        response = owner_client.post(**get_document_endpoint(document_id=document_id, space_id=space_id))

    with allure.step(f'Проверка, что статус ответа = {expected_status} и ошибка соответствующая'):
        assert response.status_code == expected_status, f'Ожидался статус {expected_status}, получен {response.status_code}'
        error = response.json().get('error')
        assert error.get(
            'code') == expected_error_code, f"Ожидался код ошибки '{expected_error_code}', получен: {error.get('code')}"