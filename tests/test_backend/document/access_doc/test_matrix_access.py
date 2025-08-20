import pytest
import allure
from test_backend.data.endpoints.Document.document_endpoints import get_document_endpoint

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


@allure.title('Проверка доступа к документам клиента')
def test_space_client_document_access(space_client, main_space, main_space_doc, main_project_doc, main_personal_doc):
    """
    Эта функция тестирует контроль доступа к документам клиента для заданного пространства. Она проверяет,
    доступен ли основной документ, и гарантирует, что проектные и личные документы недоступны в соответствии
    с ожидаемыми разрешениями.

    """
    with allure.step('Проверка доступа к основному документу MAIN_SPACE_DOC_ID'):
        response_space = space_client.post(**get_document_endpoint(document_id=main_space_doc, space_id=main_space))
        assert response_space.status_code == 200, 'Доступ к MAIN_SPACE_DOC_ID должен быть разрешён'

    with allure.step('Проверка отсутствия доступа к проектному документу MAIN_PROJECT_DOC_ID'):
        response_project = space_client.post(**get_document_endpoint(document_id=main_project_doc, space_id=main_space))
        assert response_project.status_code == 403, 'Доступ к MAIN_PROJECT_DOC_ID должен быть запрещён'

    with allure.step('Проверка отсутствия доступа к персональному документу MAIN_PERSONAL_DOC_ID'):
        response_personal = space_client.post(
            **get_document_endpoint(document_id=main_personal_doc, space_id=main_space)
        )
        assert response_personal.status_code == 403, 'Доступ к MAIN_PERSONAL_DOC_ID должен быть запрещён'


@allure.title("Проверка доступа project_client к основному документу, проектному документу и отсутствия доступа к персональному документу")
def test_project_client_document_access(project_client, main_space, main_space_doc, main_project_doc, main_personal_doc):
    """
    Проверяем, что project_client имеет доступ к main_space_doc и main_project_doc, но не имеет доступа к main_personal_doc.
    """

    with allure.step("Проверка доступа project_client к основному документу MAIN_SPACE_DOC_ID"):
        response_space = project_client.post(**get_document_endpoint(document_id=main_space_doc, space_id=main_space))
        assert response_space.status_code == 200, "Доступ к MAIN_SPACE_DOC_ID должен быть разрешён"

    with allure.step("Проверка доступа project_client к проектному документу MAIN_PROJECT_DOC_ID"):
        response_project = project_client.post(**get_document_endpoint(document_id=main_project_doc, space_id=main_space))
        assert response_project.status_code == 200, "Доступ к MAIN_PROJECT_DOC_ID должен быть разрешён"

    with allure.step("Проверка отсутствия доступа project_client к персональному документу MAIN_PERSONAL_DOC_ID"):
        response_personal = project_client.post(**get_document_endpoint(document_id=main_personal_doc, space_id=main_space))
        assert response_personal.status_code == 403, "Доступ к MAIN_PERSONAL_DOC_ID должен быть запрещён"